import secrets
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from passlib.context import CryptContext
from src.core.logic_logger import log_logic_execution
from src.repositories.cooperation import CooperationRepository, DocumentRepository
from src.services.activity import ActivityService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LinkService:
    @staticmethod
    @log_logic_execution
    async def generate_invite_code(document_id: str, current_user) -> dict:
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc bạn không phải là chủ sở hữu",
            )
        invite_code = secrets.token_hex(4).upper()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=48)
        await CooperationRepository.update_invite_code(
            {"document_id": document_id},
            {
                "$set": {
                    "invite_code": invite_code,
                    "created_by": str(current_user.id),
                    "created_at": datetime.now(timezone.utc),
                    "expires_at": expires_at,
                }
            },
            upsert=True,
        )
        await ActivityService.log_activity(
            document_id,
            current_user.full_name,
            "Create invite code",
            "A temporary invite code has been generated for collaboration onboarding",
        )
        return {
            "document_id": document_id,
            "invite_code": invite_code,
            "expires_at": expires_at.isoformat(),
        }

    @staticmethod
    @log_logic_execution
    async def join_via_invite_code(invite_code: str, current_user) -> dict:
        record = await CooperationRepository.find_invite_code(
            {"invite_code": invite_code.strip().upper()}
        )
        if not record:
            raise HTTPException(
                status_code=404, detail="Mã tham gia không hợp lệ hoặc không tồn tại"
            )
        expires_at = record.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at and expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Mã tham gia đã hết hạn hiệu lực")
        document_id = record["document_id"]
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không còn tồn tại trên hệ thống")
        if str(doc.get("creator_id")) == str(current_user.id):
            raise HTTPException(
                status_code=400, detail="Bạn đã là chủ sở hữu của tài liệu này"
            )
        coauthors = doc.get("coauthors", [])
        if str(current_user.id) in coauthors:
            return {
                "message": "Bạn đã là cộng tác viên của tài liệu này",
                "document_id": document_id,
            }
        await DocumentRepository.update_one(
            {"_id": document_id},
            {
                "$addToSet": {"coauthors": str(current_user.id)},
                "$set": {
                    f"coauthor_roles.{str(current_user.id)}": "editor",
                    "updated_at": datetime.now(timezone.utc),
                },
            },
        )
        await ActivityService.log_activity(
            document_id,
            current_user.full_name,
            "Join with code",
            "User successfully joined collaboration workspace using a valid invite code",
        )
        return {
            "message": "Gia nhập nhóm cộng tác tài liệu hoàn tất",
            "document_id": document_id,
        }

    @staticmethod
    @log_logic_execution
    async def configure_share_link(
        document_id: str,
        is_active: bool,
        password: str | None,
        default_role: str,
        expires_in_hours: int | None,
        current_user,
    ) -> dict:
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc bạn không phải là chủ sở hữu",
            )
        if default_role not in ["editor", "commenter", "viewer"]:
            raise HTTPException(status_code=400, detail="Quyền mặc định cung cấp không hợp lệ")

        existing_link = await CooperationRepository.find_share_link({"document_id": document_id})
        token = existing_link.get("share_token") if existing_link else secrets.token_urlsafe(16)

        expires_at = None
        if expires_in_hours and expires_in_hours > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

        hashed_pw = None
        if password and password.strip():
            hashed_pw = pwd_context.hash(password.strip())
        elif existing_link and password is None:
            hashed_pw = existing_link.get("password_hash")

        update_doc = {
            "document_id": document_id,
            "share_token": token,
            "is_active": is_active,
            "password_hash": hashed_pw,
            "has_password": bool(hashed_pw),
            "default_role": default_role,
            "expires_at": expires_at,
            "created_by": str(current_user.id),
            "updated_at": datetime.now(timezone.utc),
        }

        await CooperationRepository.update_share_link(
            {"document_id": document_id},
            {"$set": update_doc},
            upsert=True,
        )

        await ActivityService.log_activity(
            document_id,
            current_user.full_name,
            "Configure share link",
            f"Public collaboration link state updated: active={is_active}, role={default_role}, password_protected={bool(hashed_pw)}",
        )

        return {
            "document_id": document_id,
            "share_token": token,
            "is_active": is_active,
            "has_password": bool(hashed_pw),
            "default_role": default_role,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "message": "Cấu hình liên kết cộng tác hoàn tất",
        }

    @staticmethod
    @log_logic_execution
    async def get_share_link_config(document_id: str, current_user) -> dict:
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc bạn không phải là chủ sở hữu",
            )
        link = await CooperationRepository.find_share_link({"document_id": document_id})
        if not link:
            return {
                "document_id": document_id,
                "is_active": False,
                "share_token": None,
                "has_password": False,
                "default_role": "editor",
                "expires_at": None,
            }
        return {
            "document_id": document_id,
            "is_active": link.get("is_active", False),
            "share_token": link.get("share_token"),
            "has_password": bool(link.get("has_password", False)),
            "default_role": link.get("default_role", "editor"),
            "expires_at": (
                link["expires_at"].isoformat()
                if isinstance(link.get("expires_at"), datetime)
                else link.get("expires_at")
            ),
        }

    @staticmethod
    @log_logic_execution
    async def get_public_share_link_info(share_token: str) -> dict:
        link = await CooperationRepository.find_share_link({"share_token": share_token})
        if not link or not link.get("is_active"):
            raise HTTPException(
                status_code=404, detail="Liên kết chia sẻ không tồn tại hoặc đã bị đóng"
            )
        expires_at = link.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at and expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Liên kết chia sẻ đã hết hạn")
        doc = await DocumentRepository.find_one({"_id": link["document_id"]})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu liên quan không tồn tại")
        return {
            "document_id": doc["_id"],
            "title": doc.get("title", "Untitled Document"),
            "description": doc.get("description", ""),
            "has_password": bool(link.get("has_password", False)),
            "default_role": link.get("default_role", "editor"),
            "created_at": (
                doc.get("created_at").isoformat()
                if isinstance(doc.get("created_at"), datetime)
                else str(doc.get("created_at", ""))
            ),
        }

    @staticmethod
    @log_logic_execution
    async def join_via_share_link(
        share_token: str, password: str | None, current_user
    ) -> dict:
        link = await CooperationRepository.find_share_link({"share_token": share_token})
        if not link or not link.get("is_active"):
            raise HTTPException(
                status_code=404, detail="Liên kết chia sẻ không tồn tại hoặc đã bị vô hiệu hóa"
            )
        expires_at = link.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at and expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Liên kết chia sẻ đã hết hạn hiệu lực")

        if link.get("has_password") and link.get("password_hash"):
            if not password or not pwd_context.verify(password.strip(), link["password_hash"]):
                raise HTTPException(status_code=403, detail="Mật khẩu truy cập liên kết không chính xác")

        document_id = link["document_id"]
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không còn tồn tại trên hệ thống")

        if str(doc.get("creator_id")) == str(current_user.id):
            return {
                "message": "Bạn là chủ sở hữu của tài liệu này",
                "document_id": document_id,
            }

        coauthors = doc.get("coauthors", [])
        role = link.get("default_role", "editor")

        if str(current_user.id) in coauthors:
            return {
                "message": "Bạn đã là thành viên cộng tác của tài liệu này",
                "document_id": document_id,
            }

        await DocumentRepository.update_one(
            {"_id": document_id},
            {
                "$addToSet": {"coauthors": str(current_user.id)},
                "$set": {
                    f"coauthor_roles.{str(current_user.id)}": role,
                    "updated_at": datetime.now(timezone.utc),
                },
            },
        )

        await ActivityService.log_activity(
            document_id,
            current_user.full_name,
            "Join via share link",
            f"User joined collaborative session with role {role} via public share link",
        )

        return {
            "message": "Gia nhập nhóm cộng tác tài liệu qua liên kết hoàn tất",
            "document_id": document_id,
            "role": role,
        }
