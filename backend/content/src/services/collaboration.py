from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.repositories.document import DocumentRepository
from src.repositories.collaboration import CollaborationRepository
from src.repositories.collaboration import CollaborationRepository
from src.repositories.collaboration import CollaborationRepository
from src.repositories.collaboration import CollaborationRepository
from src.repositories.collaboration import CollaborationRepository
from src.repositories.collaboration import CollaborationRepository
from src.repositories.collaboration import CollaborationRepository
from src.repositories.collaboration import CollaborationRepository
from src.repositories.collaboration import CollaborationRepository

class CollaborationService:

    @staticmethod
    @log_logic_execution
    async def log_activity(
        document_id: str, user_name: str, action: str, details: str
    ):
        await CollaborationRepository.insert_activity(
            {
                "_id": str(uuid7()),
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
                    f"{settings.MANAGEMENT_URL}/nguoi-dung/email/{invitee_email}",
                )
                if resp.status_code == 200:
                    invitee = resp.json().get("data")
        except Exception:
            pass
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
            "_id": str(uuid7()),
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
        logger.info("Collaboration invitation processed and sent successfully")
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
            .execute()
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
        logger.info("Collaboration invitation response processed successfully")
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
            .execute()
        )
        collaborators = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for inv in invites:
                    user_info = None
                    try:
                        resp = await client.get(
                            f"{settings.MANAGEMENT_URL}/nguoi-dung/{inv['invitee_id']}",
                        )
                        if resp.status_code == 200:
                            user_info = resp.json().get("data")
                    except Exception:
                        pass
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
            pass
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
        logger.info("Collaborator removed successfully")
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
            .execute()
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
                    f"{settings.MANAGEMENT_URL}/nguoi-dung/{target_user_id}",
                )
                if resp.status_code == 200:
                    target_user = resp.json().get("data")
        except Exception:
            pass
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
        logger.info("Document ownership transferred successfully")
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
        if role not in ["editor", "viewer"]:
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
            "_id": str(uuid7()),
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
            .execute()
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
            .execute()
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
            .execute()
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
            "_id": str(uuid7()),
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
            .execute()
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
        invite_code = str(uuid7())[:8].upper()
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
                "_id": str(uuid7()),
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
            "_id": str(uuid7()),
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
            .execute()
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
            "_id": str(uuid7()),
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
            .execute()
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
