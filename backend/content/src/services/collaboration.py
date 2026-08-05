from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext

import httpx
from fastapi import HTTPException
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.repositories.document import DocumentRepository
from src.repositories.collaboration import CollaborationRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CollaborationService:

    @staticmethod
    @log_logic_execution
    async def log_activity(
        document_id: str, user_name: str, action: str, details: str
    ):
        await CollaborationRepository.insert_activity(
            {
                "_id": str(uuid.uuid4()),
                "document_id": document_id,
                "user_name": user_name,
                "action": action,
                "details": details,
                "timestamp": datetime.now(timezone.utc),
            }
        )

    @staticmethod
    @log_logic_execution
    async def send_collaboration_invite(
        document_id: str, invitee_email: str, role: str, current_user
    ) -> dict:
        if role not in ["editor", "commenter", "viewer"]:
            raise HTTPException(status_code=400, detail="Phân quyền truy cập cung cấp không hợp lệ")
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Hệ thống không tìm thấy tài liệu yêu cầu hoặc bạn không có quyền truy cập",
            )
        invitee = None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{settings.HUMANITY_URL}/nguoi-dung/email/{invitee_email}",
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
                if resp.status_code == 200:
                    invitee = resp.json().get("data")
        except Exception:
            logger.exception("Failed to retrieve collaboration invitee")
            raise HTTPException(status_code=503, detail="Dịch vụ hồ sơ người dùng tạm thời không khả dụng")
        if not invitee:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy người dùng được yêu cầu")
        invitee_id = str(invitee["_id"])
        if invitee_id == str(current_user.id):
            raise HTTPException(
                status_code=400, detail="Thao tác không hợp lệ: Không thể gửi lời mời cộng tác cho chính chủ sở hữu"
            )
        existing_invite = await CollaborationRepository.find_invite(
            {"document_id": document_id, "invitee_id": invitee_id, "status": "PENDING"}
        )
        if existing_invite:
            raise HTTPException(
                status_code=400, detail="Lời mời cộng tác đã được gửi trước đó và đang chờ phản hồi"
            )
        coauthors = doc.get("coauthors", [])
        if invitee_id in coauthors:
            raise HTTPException(
                status_code=400, detail="Tài khoản yêu cầu đã là thành viên cộng tác của tài liệu này"
            )
        invite = {
            "_id": str(uuid.uuid4()),
            "document_id": document_id,
            "document_title": doc.get("title", "Untitled Document"),
            "inviter_id": str(current_user.id),
            "inviter_name": current_user.full_name,
            "invitee_id": invitee_id,
            "role": role,
            "status": "PENDING",
            "created_at": datetime.now(timezone.utc),
        }
        await CollaborationRepository.insert_invite(invite)
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Send invitation",
            "A new editorial collaboration invitation has been processed and dispatched via the internal notification system",
        )
        logger.info("Collaboration invitation processed and sent")
        return {
            "message": "Xử lý và gửi lời mời tham gia cộng tác hoàn tất",
            "invite_id": invite["_id"],
        }

    @staticmethod
    @log_logic_execution
    async def get_my_collaboration_invites(current_user) -> list:
        invites = (
            await mongo
            .find("collaboration_invites", {"invitee_id": str(current_user.id), "status": "PENDING"})
            .sort("created_at", -1)
            .to_list(length=None)
        )
        return invites

    @staticmethod
    @log_logic_execution
    async def respond_to_collaboration_invite(
        invite_id: str, status: str, current_user
    ) -> dict:
        invite = await CollaborationRepository.find_invite(
            {"_id": invite_id, "invitee_id": str(current_user.id), "status": "PENDING"}
        )
        if not invite:
            raise HTTPException(
                status_code=404,
                detail="Lời mời cộng tác không hợp lệ, đã hết hạn hoặc đã được xử lý trước đó",
            )
        if status not in ["ACCEPTED", "REJECTED"]:
            raise HTTPException(
                status_code=400, detail="Trạng thái phản hồi cung cấp không hợp lệ"
            )
        await CollaborationRepository.update_invite(
            {"_id": invite_id},
            {"$set": {"status": status, "responded_at": datetime.now(timezone.utc)}},
        )
        if status == "ACCEPTED":
            await DocumentRepository.update_one(
                {"_id": invite["document_id"]},
                {
                    "$push": {"coauthors": str(current_user.id)},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
            )
        await CollaborationService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Accepted" if status == "ACCEPTED" else "Declined",
            "The recipient has officially registered their response to the pending editorial collaboration invitation",
        )
        logger.info("Collaboration invitation response processed")
        return {"message": "Ghi nhận trạng thái phản hồi lời mời cộng tác hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def get_collaborators(document_id: str, current_user) -> list:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Hệ thống không tìm thấy tài liệu yêu cầu hoặc bạn không có quyền truy cập",
            )
        invites = (
            await mongo
            .find("collaboration_invites", {"document_id": document_id, "status": "ACCEPTED"})
            .to_list(length=None)
        )
        collaborators = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for inv in invites:
                    user_info = None
                    try:
                        resp = await client.get(
                            f"{settings.HUMANITY_URL}/nguoi-dung/{inv['invitee_id']}",
                            headers={"X-Internal-Token": settings.SECRET_KEY},
                        )
                        if resp.status_code == 200:
                            user_info = resp.json().get("data")
                    except Exception:
                        logger.warning("Failed to retrieve a collaborator profile")
                    if user_info:
                        collaborators.append(
                            {
                                "collaboration_id": inv["_id"],
                                "user_id": inv["invitee_id"],
                                "email": user_info.get("email", ""),
                                "full_name": user_info.get("full_name", "User"),
                                "role": inv.get("role", "editor"),
                            }
                        )
        except Exception:
            logger.exception("Failed to retrieve collaborator profiles")
            raise HTTPException(status_code=503, detail="Dịch vụ hồ sơ người dùng tạm thời không khả dụng")
        return collaborators

    @staticmethod
    @log_logic_execution
    async def remove_collaborator(collaboration_id: str, current_user) -> dict:
        invite = await CollaborationRepository.find_invite(
            {"_id": collaboration_id}
        )
        if not invite:
            raise HTTPException(
                status_code=404, detail="Hệ thống gặp sự cố khi tải cấu hình môi trường cộng tác"
            )
        doc = await DocumentRepository.find_one(
            {"_id": invite["document_id"], "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền quản lý danh sách thành viên cộng tác",
            )
        await DocumentRepository.update_one(
            {"_id": invite["document_id"]},
            {"$pull": {"coauthors": invite["invitee_id"]}},
        )
        await CollaborationRepository.delete_invite(
            {"_id": collaboration_id}
        )
        await CollaborationService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Collaborator removed",
            "The specified collaborator has been effectively removed from the authorized modification list",
        )
        logger.info("Collaborator removed")
        return {"message": "Đã thu hồi quyền và xóa thành viên khỏi danh sách cộng tác"}

    @staticmethod
    @log_logic_execution
    async def get_activities(document_id: str, current_user) -> list:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        activities = (
            await mongo
            .find("collaboration_activities", {"document_id": document_id})
            .sort("timestamp", -1)
            .limit(50)
            .to_list(length=50)
        )
        return [
            {
                "id": act["_id"],
                "user_name": act["user_name"],
                "action": act["action"],
                "details": act["details"],
                "timestamp": (
                    act["timestamp"].isoformat()
                    if isinstance(act.get("timestamp"), datetime)
                    else act.get("timestamp")
                ),
            }
            for act in activities
        ]

    @staticmethod
    @log_logic_execution
    async def transfer_ownership(
        document_id: str, target_user_id: str, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        target_user = None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{settings.HUMANITY_URL}/nguoi-dung/{target_user_id}",
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
                if resp.status_code == 200:
                    target_user = resp.json().get("data")
        except Exception:
            logger.exception("Failed to retrieve ownership transfer target")
            raise HTTPException(status_code=503, detail="Dịch vụ hồ sơ người dùng tạm thời không khả dụng")
        if not target_user:
            raise HTTPException(
                status_code=404,
                detail="Hệ thống không tìm thấy tài khoản để chuyển quyền sở hữu",
            )
        if target_user_id not in doc.get("coauthors", []):
            raise HTTPException(
                status_code=400,
                detail="Chỉ có thể chuyển quyền sở hữu cho thành viên đang cộng tác",
            )
        await DocumentRepository.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "creator_id": target_user_id,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$pull": {"coauthors": target_user_id},
            },
        )
        await DocumentRepository.update_one(
            {"_id": document_id}, {"$push": {"coauthors": str(current_user.id)}}
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Transfer ownership",
            "The primary administrative ownership rights of the document have been securely reassigned",
        )
        logger.info("Document ownership transferred")
        return {"message": "Cập nhật và chuyển giao quyền sở hữu tài liệu hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def update_status(document_id: str, current_user) -> dict:
        await CollaborationRepository.update_status(
            {"document_id": document_id, "user_id": str(current_user.id)},
            {
                "$set": {
                    "last_seen": datetime.now(timezone.utc),
                    "full_name": current_user.full_name,
                }
            },
            upsert=True,
        )
        return {"message": "Đồng bộ hóa trạng thái hoạt động trực tuyến hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def get_online_collaborators(document_id: str) -> list:
        cutoff = datetime.now(timezone.utc).timestamp() - 60
        online_users = (
            await mongo
            .find("collaboration_status", {"document_id": document_id})
            .to_list(length=None)
        )
        result = []
        for u in online_users:
            last_seen = u.get("last_seen")
            last_seen_ts = (
                last_seen.timestamp() if isinstance(last_seen, datetime) else 0
            )
            is_online = last_seen_ts > cutoff
            result.append(
                {
                    "user_id": u["user_id"],
                    "full_name": u.get("full_name", "Collaborator"),
                    "status": "online" if is_online else "offline",
                }
            )
        return result

    @staticmethod
    @log_logic_execution
    async def update_collaborator_role(
        collaboration_id: str, role: str, current_user
    ) -> dict:
        invite = await CollaborationRepository.find_invite(
            {"_id": collaboration_id}
        )
        if not invite:
            raise HTTPException(
                status_code=404, detail="Lỗi tải cấu hình môi trường cộng tác"
            )
        doc = await DocumentRepository.find_one(
            {"_id": invite["document_id"], "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=403,
                detail="Không có quyền quản lý người tham gia",
            )
        if role not in ["editor", "commenter", "viewer"]:
            raise HTTPException(status_code=400, detail="Phân quyền truy cập cung cấp không hợp lệ")
        await CollaborationRepository.update_invite(
            {"_id": collaboration_id}, {"$set": {"role": role}}
        )
        await CollaborationService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Update role",
            "The specific access privileges and system roles for the collaborator have been modified",
        )
        return {"message": "Cập nhật cấu hình phân quyền cộng tác viên hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def send_memo(document_id: str, message: str, current_user) -> dict:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        memo = {
            "_id": str(uuid.uuid4()),
            "document_id": document_id,
            "sender_name": current_user.full_name,
            "sender_id": str(current_user.id),
            "message": message,
            "timestamp": datetime.now(timezone.utc),
        }
        await CollaborationRepository.insert_memo(memo)
        return {"message": "Phân phối tin nhắn cộng tác nội bộ hoàn tất", "memo": memo}

    @staticmethod
    @log_logic_execution
    async def get_memos(document_id: str, current_user) -> list:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        memos = (
            await mongo
            .find("collaboration_memos", {"document_id": document_id})
            .sort("timestamp", 1)
            .limit(100)
            .to_list(length=100)
        )
        return [
            {
                "id": m["_id"],
                "sender_name": m["sender_name"],
                "sender_id": m["sender_id"],
                "message": m["message"],
                "timestamp": (
                    m["timestamp"].isoformat()
                    if isinstance(m.get("timestamp"), datetime)
                    else m.get("timestamp")
                ),
            }
            for m in memos
        ]

    @staticmethod
    @log_logic_execution
    async def update_collab_access(
        document_id: str, access_level: str, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        if access_level not in ["invite_only", "anyone_with_link"]:
            raise HTTPException(
                status_code=400, detail="Cấu hình mức độ truy cập cộng tác không hợp lệ"
            )
        await DocumentRepository.update_one(
            {"_id": document_id}, {"$set": {"collab_access_level": access_level}}
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Permission settings",
            "The core collaborative access permissions for the environment have been successfully adjusted",
        )
        return {
            "message": "Cập nhật cấu hình mức độ quyền truy cập cộng tác hoàn tất",
            "collab_access_level": access_level,
        }

    @staticmethod
    @log_logic_execution
    async def get_sent_pending_invites(document_id: str, current_user) -> list:
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        invites = (
            await mongo
            .find("collaboration_invites", {"document_id": document_id, "status": "PENDING"})
            .sort("created_at", -1)
            .to_list(length=None)
        )
        return invites

    @staticmethod
    @log_logic_execution
    async def revoke_invite(invite_id: str, current_user) -> dict:
        invite = await CollaborationRepository.find_invite(
            {"_id": invite_id, "status": "PENDING"}
        )
        if not invite:
            raise HTTPException(
                status_code=404,
                detail="Hệ thống không tìm thấy lời mời cộng tác yêu cầu hoặc lời mời đã được xử lý",
            )
        doc = await DocumentRepository.find_one(
            {"_id": invite["document_id"], "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="Bạn không có quyền thu hồi lời mời cộng tác này"
            )
        await CollaborationRepository.delete_invite(
            {"_id": invite_id}
        )
        await CollaborationService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Invitation revoked",
            "The active collaboration invitation token has been securely invalidated by the document owner",
        )
        return {"message": "Hủy bỏ và thu hồi lời mời tham gia cộng tác hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def get_contribution_stats(document_id: str, current_user) -> list:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        pipeline = [
            {"$match": {"document_id": document_id}},
            {"$group": {"_id": "$user_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        stats = (
            await mongo
            .aggregate("collaboration_activities", pipeline)
            .to_list(length=None)
        )
        return [{"user_name": s["_id"], "count": s["count"]} for s in stats]

    @staticmethod
    @log_logic_execution
    async def create_snapshot(
        document_id: str, version_name: str, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        snapshot = {
            "_id": str(uuid.uuid4()),
            "document_id": document_id,
            "version_name": version_name,
            "content": doc.get("content", ""),
            "created_by": current_user.full_name,
            "timestamp": datetime.now(timezone.utc),
        }
        await CollaborationRepository.insert_draft(snapshot)
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Create draft",
            "A structural milestone snapshot has been permanently recorded in the version control history",
        )
        return {"message": "Lưu trữ bản chụp phiên bản tài liệu hoàn tất", "snapshot": snapshot}

    @staticmethod
    @log_logic_execution
    async def get_snapshots(document_id: str, current_user) -> list:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        draft = (
            await mongo
            .find("collaboration_drafts", {"document_id": document_id})
            .sort("timestamp", -1)
            .to_list(length=None)
        )
        return [
            {
                "id": d["_id"],
                "version_name": d["version_name"],
                "created_by": d["created_by"],
                "timestamp": (
                    d["timestamp"].isoformat()
                    if isinstance(d.get("timestamp"), datetime)
                    else d.get("timestamp")
                ),
            }
            for d in draft
        ]

    @staticmethod
    @log_logic_execution
    async def acquire_lock(document_id: str, current_user) -> dict:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        cutoff = datetime.now(timezone.utc).timestamp() - 60
        existing = await CollaborationRepository.find_lock(
            {"document_id": document_id}
        )
        if existing:
            locked_at = existing.get("locked_at")
            locked_at_ts = (
                locked_at.timestamp() if isinstance(locked_at, datetime) else 0
            )
            if locked_at_ts > cutoff and existing.get("user_id") != str(
                current_user.id
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Tài liệu hiện đang trong phiên chỉnh sửa độc quyền của người dùng khác",
                )
        await CollaborationRepository.update_lock(
            {"document_id": document_id},
            {
                "$set": {
                    "user_id": str(current_user.id),
                    "user_name": current_user.full_name,
                    "locked_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Document locked",
            "An exclusive access token has been acquired to prevent overlapping editorial modifications",
        )
        return {"message": "Thiết lập khóa phiên chỉnh sửa tài liệu hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def release_lock(document_id: str, current_user) -> dict:
        existing = await CollaborationRepository.find_lock(
            {"document_id": document_id}
        )
        if existing and existing.get("user_id") == str(current_user.id):
            await CollaborationRepository.delete_lock(
                {"document_id": document_id}
            )
            await CollaborationService.log_activity(
                document_id,
                current_user.full_name,
                "Unlock document",
                "The previously acquired exclusive editorial lock has been safely released back into the available pool",
            )
        return {"message": "Hủy khóa phiên chỉnh sửa tài liệu hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def get_lock_status(document_id: str) -> dict:
        existing = await CollaborationRepository.find_lock(
            {"document_id": document_id}
        )
        if not existing:
            return {"is_locked": False}
        cutoff = datetime.now(timezone.utc).timestamp() - 60
        locked_at = existing.get("locked_at")
        locked_at_ts = locked_at.timestamp() if isinstance(locked_at, datetime) else 0
        is_locked = locked_at_ts > cutoff
        if not is_locked:
            return {"is_locked": False}
        return {
            "is_locked": True,
            "user_id": existing.get("user_id"),
            "user_name": existing.get("user_name"),
            "locked_at": (
                existing.get("locked_at").isoformat()
                if isinstance(existing.get("locked_at"), datetime)
                else None
            ),
        }

    @staticmethod
    @log_logic_execution
    async def generate_invite_code(document_id: str, current_user) -> dict:
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        invite_code = secrets.token_hex(8).upper()
        await CollaborationRepository.update_invite_code(
            {"document_id": document_id},
            {
                "$set": {
                    "invite_code": invite_code,
                    "created_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Generate collaboration code",
            "A secure time-limited invitation token has been successfully generated for immediate collaborative access",
        )
        return {"invite_code": invite_code}

    @staticmethod
    @log_logic_execution
    async def join_via_invite_code(invite_code: str, current_user) -> dict:
        code_entry = await CollaborationRepository.find_invite_code(
            {"invite_code": invite_code.upper()}
        )
        if not code_entry:
            raise HTTPException(
                status_code=404, detail="Mã mời tham gia cộng tác không hợp lệ hoặc đã quá hạn sử dụng"
            )
        document_id = code_entry["document_id"]
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu yêu cầu")
        if doc.get("creator_id") == str(current_user.id):
            raise HTTPException(
                status_code=400, detail="Bạn hiện là chủ sở hữu chính của tài liệu này"
            )
        if str(current_user.id) in doc.get("coauthors", []):
            raise HTTPException(status_code=400, detail="Bạn hiện đã là thành viên trong không gian cộng tác của tài liệu này")
        await DocumentRepository.update_one(
            {"_id": document_id},
            {
                "$push": {"coauthors": str(current_user.id)},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        await CollaborationRepository.insert_invite(
            {
                "_id": str(uuid.uuid4()),
                "document_id": document_id,
                "document_title": doc.get("title", "Untitled Document"),
                "inviter_id": doc["creator_id"],
                "inviter_name": "Owner",
                "invitee_id": str(current_user.id),
                "role": "editor",
                "status": "ACCEPTED",
                "created_at": datetime.now(timezone.utc),
                "responded_at": datetime.now(timezone.utc),
            }
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Join via code",
            "The authenticated user has successfully claimed the invitation token and entered the editorial workspace",
        )
        return {
            "message": "Tham gia không gian cộng tác tài liệu hoàn tất",
            "document_id": document_id,
        }

    @staticmethod
    @log_logic_execution
    async def create_task(
        document_id: str, task_desc: str, assigned_to: str, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        task = {
            "_id": str(uuid.uuid4()),
            "document_id": document_id,
            "task_desc": task_desc,
            "is_done": False,
            "assigned_to": assigned_to or "Unassigned",
            "created_by": current_user.full_name,
            "created_at": datetime.now(timezone.utc),
        }
        await CollaborationRepository.insert_task(task)
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Create task",
            "A structured operational assignment has been successfully integrated into the active workflow queue",
        )
        return {"task": task}

    @staticmethod
    @log_logic_execution
    async def get_tasks(document_id: str, current_user) -> list:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        tasks = (
            await mongo
            .find("collaboration_tasks", {"document_id": document_id})
            .sort("created_at", -1)
            .to_list(length=None)
        )
        return [
            {
                "id": t["_id"],
                "task_desc": t["task_desc"],
                "is_done": t["is_done"],
                "assigned_to": t["assigned_to"],
                "created_by": t["created_by"],
                "created_at": (
                    t["created_at"].isoformat()
                    if isinstance(t.get("created_at"), datetime)
                    else t.get("created_at")
                ),
            }
            for t in tasks
        ]

    @staticmethod
    @log_logic_execution
    async def update_task(task_id: str, is_done: bool, current_user) -> dict:
        task = await CollaborationRepository.find_task(
            {"_id": task_id}
        )
        if not task:
            raise HTTPException(
                status_code=404, detail="Hệ thống không tìm thấy nhiệm vụ cộng tác yêu cầu"
            )
        doc = await DocumentRepository.find_one(
            {
                "_id": task["document_id"],
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="Bạn không có quyền chỉnh sửa nhiệm vụ cộng tác này"
            )
        await CollaborationRepository.update_task(
            {"_id": task_id}, {"$set": {"is_done": is_done}}
        )
        await CollaborationService.log_activity(
            task["document_id"],
            current_user.full_name,
            "Update task",
            "The execution status of the designated collaborative task has been formally modified",
        )
        return {"message": "Cập nhật trạng thái thực thi nhiệm vụ cộng tác hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def add_task_comment(
        task_id: str, comment_text: str, current_user
    ) -> dict:
        task = await CollaborationRepository.find_task(
            {"_id": task_id}
        )
        if not task:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy nhiệm vụ cộng tác"
            )
        doc = await DocumentRepository.find_one(
            {
                "_id": task["document_id"],
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="Bạn không có quyền tham gia thảo luận trong nhiệm vụ này"
            )
        comment = {
            "_id": str(uuid.uuid4()),
            "task_id": task_id,
            "sender_name": current_user.full_name,
            "comment_text": comment_text,
            "timestamp": datetime.now(timezone.utc),
        }
        await CollaborationRepository.insert_task_comment(comment)
        return {"comment": comment}

    @staticmethod
    @log_logic_execution
    async def get_task_comments(task_id: str, current_user) -> list:
        task = await CollaborationRepository.find_task(
            {"_id": task_id}
        )
        if not task:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy nhiệm vụ cộng tác"
            )
        doc = await DocumentRepository.find_one(
            {
                "_id": task["document_id"],
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="Không có quyền thảo luận trong nhiệm vụ này"
            )
        comments = (
            await mongo
            .find("collaboration_task_comments", {"task_id": task_id})
            .sort("timestamp", 1)
            .to_list(length=None)
        )
        return [
            {
                "id": c["_id"],
                "sender_name": c["sender_name"],
                "comment_text": c["comment_text"],
                "timestamp": (
                    c["timestamp"].isoformat()
                    if isinstance(c.get("timestamp"), datetime)
                    else c.get("timestamp")
                ),
            }
            for c in comments
        ]

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
                detail="Không tìm thấy tài liệu hoặc bạn không có quyền cấu hình liên kết",
            )
        existing = await CollaborationRepository.find_share_link(
            {"document_id": document_id}
        )
        share_token = (
            existing.get("share_token") if existing else secrets.token_urlsafe(16)
        )
        password_hash = existing.get("password_hash") if existing else None
        is_pw_protected = (
            existing.get("is_password_protected", False) if existing else False
        )
        if password is not None:
            if password.strip():
                password_hash = pwd_context.hash(password.strip())
                is_pw_protected = True
            else:
                password_hash = None
                is_pw_protected = False

        expires_at = None
        if expires_in_hours and expires_in_hours > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        elif existing and existing.get("expires_at") and expires_in_hours is None:
            expires_at = existing.get("expires_at")

        link_record = {
            "document_id": document_id,
            "share_token": share_token,
            "is_active": is_active,
            "is_password_protected": is_pw_protected,
            "password_hash": password_hash,
            "default_role": default_role,
            "expires_at": expires_at,
            "updated_at": datetime.now(timezone.utc),
        }
        if not existing:
            link_record["created_at"] = datetime.now(timezone.utc)

        await CollaborationRepository.update_share_link(
            {"document_id": document_id},
            {"$set": link_record},
            upsert=True,
        )

        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Configure share link",
            "Updated collaboration share link settings and access requirements",
        )

        return {
            "document_id": document_id,
            "share_token": share_token,
            "is_active": is_active,
            "is_password_protected": is_pw_protected,
            "default_role": default_role,
            "expires_at": (
                expires_at.isoformat()
                if isinstance(expires_at, datetime)
                else None
            ),
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
                detail="Không tìm thấy tài liệu hoặc bạn không có quyền xem cấu hình liên kết",
            )
        existing = await CollaborationRepository.find_share_link(
            {"document_id": document_id}
        )
        if not existing:
            return {
                "document_id": document_id,
                "share_token": None,
                "is_active": False,
                "is_password_protected": False,
                "default_role": "editor",
                "expires_at": None,
            }
        expires_at = existing.get("expires_at")
        return {
            "document_id": document_id,
            "share_token": existing.get("share_token"),
            "is_active": existing.get("is_active", True),
            "is_password_protected": existing.get("is_password_protected", False),
            "default_role": existing.get("default_role", "editor"),
            "expires_at": (
                expires_at.isoformat()
                if isinstance(expires_at, datetime)
                else None
            ),
        }

    @staticmethod
    @log_logic_execution
    async def get_public_share_link_info(share_token: str) -> dict:
        link = await CollaborationRepository.find_share_link(
            {"share_token": share_token}
        )
        if not link or not link.get("is_active"):
            raise HTTPException(
                status_code=404,
                detail="Liên kết chia sẻ cộng tác không tồn tại hoặc đã bị tắt",
            )
        expires_at = link.get("expires_at")
        if expires_at:
            exp_ts = (
                expires_at.timestamp()
                if isinstance(expires_at, datetime)
                else 0
            )
            if exp_ts < datetime.now(timezone.utc).timestamp():
                raise HTTPException(
                    status_code=400,
                    detail="Liên kết chia sẻ cộng tác đã quá thời hạn sử dụng",
                )
        doc = await DocumentRepository.find_one({"_id": link["document_id"]})
        if not doc:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài liệu liên kết"
            )
        return {
            "document_id": link["document_id"],
            "document_title": doc.get("title", "Untitled Document"),
            "is_password_protected": link.get("is_password_protected", False),
            "default_role": link.get("default_role", "editor"),
        }

    @staticmethod
    @log_logic_execution
    async def join_via_share_link(
        share_token: str, password: str | None, current_user
    ) -> dict:
        link = await CollaborationRepository.find_share_link(
            {"share_token": share_token}
        )
        if not link or not link.get("is_active"):
            raise HTTPException(
                status_code=404,
                detail="Liên kết chia sẻ cộng tác không tồn tại hoặc đã bị vô hiệu hóa",
            )
        expires_at = link.get("expires_at")
        if expires_at:
            exp_ts = (
                expires_at.timestamp()
                if isinstance(expires_at, datetime)
                else 0
            )
            if exp_ts < datetime.now(timezone.utc).timestamp():
                raise HTTPException(
                    status_code=400,
                    detail="Liên kết chia sẻ cộng tác đã hết hạn sử dụng",
                )
        if link.get("is_password_protected"):
            if not password:
                raise HTTPException(
                    status_code=400,
                    detail="Vui lòng cung cấp mật khẩu để tham gia không gian cộng tác",
                )
            if not pwd_context.verify(password, link.get("password_hash", "")):
                raise HTTPException(
                    status_code=403,
                    detail="Mật khẩu truy cập không gian cộng tác không chính xác",
                )
        document_id = link["document_id"]
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
        status_info = CollaborationService.get_effective_collaboration_status(
            doc, user_id=str(current_user.id), is_admin=getattr(current_user, "role", None) == "admin"
        )
        if status_info["is_effective_closed"]:
            raise HTTPException(status_code=403, detail="Tài liệu đã đóng hoàn toàn không gian cộng tác")
        if doc.get("creator_id") == str(current_user.id):
            return {
                "message": "Bạn là chủ sở hữu chính của tài liệu này",
                "document_id": document_id,
                "role": "owner",
            }
        role = link.get("default_role", "editor")
        user_id = str(current_user.id)
        if user_id not in doc.get("coauthors", []):
            await DocumentRepository.update_one(
                {"_id": document_id},
                {
                    "$push": {"coauthors": user_id},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
            )
        await CollaborationRepository.update_invite(
            {"document_id": document_id, "invitee_id": user_id},
            {
                "$set": {
                    "document_id": document_id,
                    "document_title": doc.get("title", "Untitled Document"),
                    "inviter_id": doc["creator_id"],
                    "inviter_name": "Shared Link",
                    "invitee_id": user_id,
                    "role": role,
                    "status": "ACCEPTED",
                    "responded_at": datetime.now(timezone.utc),
                },
                "$setOnInsert": {
                    "_id": str(uuid.uuid4()),
                    "created_at": datetime.now(timezone.utc),
                },
            },
            upsert=True,
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Join via share link",
            f"Joined collaboration room with role {role}",
        )
        return {
            "message": "Gia nhập không gian cộng tác thành công",
            "document_id": document_id,
            "role": role,
        }

    @staticmethod
    @log_logic_execution
    async def create_access_request(
        document_id: str, requested_role: str, message: str | None, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài liệu yêu cầu"
            )
        user_id = str(current_user.id)
        status_info = CollaborationService.get_effective_collaboration_status(
            doc, user_id=user_id, is_admin=getattr(current_user, "role", None) == "admin"
        )
        if status_info["is_effective_closed"]:
            raise HTTPException(
                status_code=403,
                detail="Tài liệu đã đóng hoàn toàn và không tiếp nhận yêu cầu xin quyền",
            )

        if doc.get("creator_id") == user_id:
            raise HTTPException(
                status_code=400, detail="Bạn là chủ sở hữu chính của tài liệu này"
            )
        if user_id in doc.get("coauthors", []):
            raise HTTPException(
                status_code=400,
                detail="Bạn đã là thành viên trong không gian cộng tác của tài liệu này",
            )
        pending = await CollaborationRepository.find_access_request(
            {"document_id": document_id, "user_id": user_id, "status": "PENDING"}
        )
        if pending:
            raise HTTPException(
                status_code=400,
                detail="Yêu cầu xin quyền cộng tác của bạn đang chờ chủ tài liệu phê duyệt",
            )
        req_doc = {
            "_id": str(uuid.uuid4()),
            "document_id": document_id,
            "document_title": doc.get("title", "Untitled Document"),
            "creator_id": doc["creator_id"],
            "user_id": user_id,
            "user_name": current_user.full_name,
            "user_email": getattr(current_user, "email", ""),
            "requested_role": requested_role,
            "message": message or "",
            "status": "PENDING",
            "created_at": datetime.now(timezone.utc),
        }
        await CollaborationRepository.insert_access_request(req_doc)
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Request collaboration access",
            f"Requested {requested_role} role access to document",
        )
        return {
            "message": "Gửi yêu cầu xin tham gia cộng tác hoàn tất",
            "request_id": req_doc["_id"],
        }

    @staticmethod
    @log_logic_execution
    async def get_document_access_requests(document_id: str, current_user) -> list:
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc bạn không có quyền xem yêu cầu",
            )
        cursor = CollaborationRepository.find_access_requests(
            {"document_id": document_id, "status": "PENDING"}
        ).sort("created_at", -1)
        items = await cursor.to_list(length=None)
        return [
            {
                "id": str(item["_id"]),
                "document_id": item["document_id"],
                "document_title": item.get("document_title", ""),
                "user_id": item["user_id"],
                "user_name": item.get("user_name", "Anonymous"),
                "user_email": item.get("user_email", ""),
                "requested_role": item.get("requested_role", "editor"),
                "message": item.get("message", ""),
                "status": item["status"],
                "created_at": (
                    item["created_at"].isoformat()
                    if isinstance(item.get("created_at"), datetime)
                    else item.get("created_at")
                ),
            }
            for item in items
        ]

    @staticmethod
    @log_logic_execution
    async def get_my_incoming_access_requests(current_user) -> list:
        cursor = CollaborationRepository.find_access_requests(
            {"creator_id": str(current_user.id), "status": "PENDING"}
        ).sort("created_at", -1)
        items = await cursor.to_list(length=None)
        return [
            {
                "id": str(item["_id"]),
                "document_id": item["document_id"],
                "document_title": item.get("document_title", ""),
                "user_id": item["user_id"],
                "user_name": item.get("user_name", "Anonymous"),
                "user_email": item.get("user_email", ""),
                "requested_role": item.get("requested_role", "editor"),
                "message": item.get("message", ""),
                "status": item["status"],
                "created_at": (
                    item["created_at"].isoformat()
                    if isinstance(item.get("created_at"), datetime)
                    else item.get("created_at")
                ),
            }
            for item in items
        ]

    @staticmethod
    @log_logic_execution
    async def review_access_request(
        request_id: str, status: str, role: str | None, current_user
    ) -> dict:
        req = await CollaborationRepository.find_access_request(
            {"_id": request_id}
        )
        if not req:
            raise HTTPException(
                status_code=404,
                detail="Yêu cầu xin quyền không tồn tại hoặc đã được xử lý",
            )
        if req.get("creator_id") != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền phê duyệt yêu cầu cho tài liệu này",
            )
        if req.get("status") != "PENDING":
            raise HTTPException(
                status_code=400, detail="Yêu cầu này đã được phản hồi trước đó"
            )
        if status not in ["ACCEPTED", "REJECTED"]:
            raise HTTPException(
                status_code=400, detail="Trạng thái phản hồi không hợp lệ"
            )
        final_role = role or req.get("requested_role", "editor")
        await CollaborationRepository.update_access_request(
            {"_id": request_id},
            {
                "$set": {
                    "status": status,
                    "granted_role": final_role if status == "ACCEPTED" else None,
                    "reviewed_at": datetime.now(timezone.utc),
                }
            },
        )
        if status == "ACCEPTED":
            user_id = req["user_id"]
            document_id = req["document_id"]
            doc = await DocumentRepository.find_one({"_id": document_id})
            if doc and user_id not in doc.get("coauthors", []):
                await DocumentRepository.update_one(
                    {"_id": document_id},
                    {
                        "$push": {"coauthors": user_id},
                        "$set": {"updated_at": datetime.now(timezone.utc)},
                    },
                )
            await CollaborationRepository.update_invite(
                {"document_id": document_id, "invitee_id": user_id},
                {
                    "$set": {
                        "document_id": document_id,
                        "document_title": req.get("document_title", ""),
                        "inviter_id": req["creator_id"],
                        "inviter_name": current_user.full_name,
                        "invitee_id": user_id,
                        "role": final_role,
                        "status": "ACCEPTED",
                        "responded_at": datetime.now(timezone.utc),
                    },
                    "$setOnInsert": {
                        "_id": str(uuid.uuid4()),
                        "created_at": datetime.now(timezone.utc),
                    },
                },
                upsert=True,
            )
        await CollaborationService.log_activity(
            req["document_id"],
            current_user.full_name,
            f"Review access request: {status}",
            f"Access request from {req.get('user_name')} was {status} with role {final_role}",
        )
        return {
            "message": (
                "Phê duyệt yêu cầu tham gia cộng tác hoàn tất"
                if status == "ACCEPTED"
                else "Từ chối yêu cầu tham gia cộng tác hoàn tất"
            ),
            "status": status,
            "role": final_role if status == "ACCEPTED" else None,
        }

    @staticmethod
    def get_effective_collaboration_status(
        document: dict, user_id: str | None = None, is_admin: bool = False
    ) -> dict:
        if not document:
            return {
                "mode": "CLOSED",
                "effective_mode": "CLOSED",
                "is_effective_closed": True,
                "is_read_only": True,
                "can_edit": False,
                "can_comment": False,
                "can_view": False,
            }

        creator_id = str(document.get("creator_id") or "")
        if is_admin or (user_id and str(user_id) == creator_id):
            return {
                "mode": document.get("collaboration_mode", "OPEN"),
                "effective_mode": "OPEN",
                "is_effective_closed": False,
                "is_read_only": False,
                "can_edit": True,
                "can_comment": True,
                "can_view": True,
            }

        now = datetime.now(timezone.utc)
        schedules = document.get("collaboration_schedules") or []
        active_schedules = [s for s in schedules if s.get("is_active", True)]

        effective_mode = None
        if active_schedules:
            in_window_rule = None
            for rule in active_schedules:
                start_at = rule.get("start_at")
                end_at = rule.get("end_at")
                if isinstance(start_at, str):
                    try:
                        start_at = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
                    except Exception:
                        start_at = None
                elif isinstance(start_at, datetime) and start_at.tzinfo is None:
                    start_at = start_at.replace(tzinfo=timezone.utc)

                if isinstance(end_at, str):
                    try:
                        end_at = datetime.fromisoformat(end_at.replace("Z", "+00:00"))
                    except Exception:
                        end_at = None
                elif isinstance(end_at, datetime) and end_at.tzinfo is None:
                    end_at = end_at.replace(tzinfo=timezone.utc)

                if end_at:
                    if start_at:
                        if start_at <= now <= end_at:
                            in_window_rule = rule
                            break
                    elif now <= end_at:
                        in_window_rule = rule
                        break

            if in_window_rule:
                effective_mode = in_window_rule.get("mode", "EDIT").upper()
            else:
                fallback = "READ_ONLY"
                for rule in active_schedules:
                    if rule.get("fallback_mode"):
                        fallback = rule.get("fallback_mode").upper()
                effective_mode = fallback

        if not effective_mode:
            effective_mode = str(document.get("collaboration_mode") or "OPEN").upper()

        can_view = effective_mode != "CLOSED"
        can_comment = effective_mode in ("OPEN", "COMMENT", "COMMENT_ONLY", "EDIT")
        can_edit = effective_mode in ("OPEN", "EDIT")
        is_read_only = effective_mode in ("READ_ONLY", "VIEW")
        is_effective_closed = effective_mode == "CLOSED"

        return {
            "mode": document.get("collaboration_mode", "OPEN"),
            "effective_mode": effective_mode,
            "is_effective_closed": is_effective_closed,
            "is_read_only": is_read_only,
            "can_edit": can_edit,
            "can_comment": can_comment,
            "can_view": can_view,
        }

    @staticmethod
    @log_logic_execution
    async def update_collaboration_mode(
        document_id: str, mode: str, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu")
        is_owner = str(doc.get("creator_id")) == str(current_user.id)
        is_admin = getattr(current_user, "role", None) == "admin"
        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=403,
                detail="Chỉ chủ sở hữu hoặc quản trị viên mới có quyền điều chỉnh chế độ đóng mở tài liệu",
            )
        mode = mode.upper()
        if mode not in ["OPEN", "COMMENT_ONLY", "READ_ONLY", "CLOSED"]:
            raise HTTPException(status_code=400, detail="Chế độ đóng mở tài liệu không hợp lệ")

        await DocumentRepository.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "collaboration_mode": mode,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            f"Update collaboration mode to {mode}",
            f"Document collaboration state set to {mode}",
        )
        return {
            "document_id": document_id,
            "collaboration_mode": mode,
            "message": "Cập nhật chế độ đóng mở tài liệu thành công",
        }

    @staticmethod
    @log_logic_execution
    async def get_collaboration_mode(document_id: str, current_user) -> dict:
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu")
        user_id = str(current_user.id) if current_user else None
        is_admin = getattr(current_user, "role", None) == "admin"
        status_info = CollaborationService.get_effective_collaboration_status(
            doc, user_id=user_id, is_admin=is_admin
        )
        return {
            "document_id": document_id,
            "collaboration_mode": doc.get("collaboration_mode", "OPEN"),
            "effective_status": status_info,
        }

    @staticmethod
    @log_logic_execution
    async def update_collaboration_schedules(
        document_id: str, schedules: list, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu")
        is_owner = str(doc.get("creator_id")) == str(current_user.id)
        is_admin = getattr(current_user, "role", None) == "admin"
        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=403,
                detail="Chỉ chủ sở hữu hoặc quản trị viên mới có quyền thiết lập lịch hẹn giờ",
            )
        processed_schedules = []
        for s in schedules:
            rule_id = s.get("id") or str(uuid.uuid4())
            start_at = s.get("start_at")
            end_at = s.get("end_at")
            if isinstance(start_at, datetime):
                start_at = start_at.isoformat()
            if isinstance(end_at, datetime):
                end_at = end_at.isoformat()
            processed_schedules.append(
                {
                    "id": rule_id,
                    "title": s.get("title") or "Khung giờ hẹn",
                    "start_at": start_at,
                    "end_at": end_at,
                    "mode": (s.get("mode") or "EDIT").upper(),
                    "fallback_mode": (s.get("fallback_mode") or "READ_ONLY").upper(),
                    "is_active": s.get("is_active", True),
                }
            )
        await DocumentRepository.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "collaboration_schedules": processed_schedules,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        await CollaborationService.log_activity(
            document_id,
            current_user.full_name,
            "Update collaboration schedules",
            f"Configured {len(processed_schedules)} schedule windows",
        )
        return {
            "document_id": document_id,
            "schedules": processed_schedules,
            "message": "Cập nhật lịch hẹn giờ quyền hạn cộng tác thành công",
        }

    @staticmethod
    @log_logic_execution
    async def get_collaboration_schedules(document_id: str, current_user) -> dict:
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu")
        user_id = str(current_user.id) if current_user else None
        is_admin = getattr(current_user, "role", None) == "admin"
        status_info = CollaborationService.get_effective_collaboration_status(
            doc, user_id=user_id, is_admin=is_admin
        )
        return {
            "document_id": document_id,
            "schedules": doc.get("collaboration_schedules") or [],
            "effective_status": status_info,
        }


