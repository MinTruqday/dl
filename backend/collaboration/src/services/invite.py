import uuid
from datetime import datetime, timezone
import httpx
from fastapi import HTTPException
from loguru import logger
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.mongo import mongo
from src.repositories.cooperation import CooperationRepository, DocumentRepository
from src.services.activity import ActivityService

class InviteService:
    @staticmethod
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
        existing_invite = await CooperationRepository.find_invite(
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
        await CooperationRepository.insert_invite(invite)
        await ActivityService.log_activity(
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
    async def get_my_collaboration_invites(current_user) -> list:
        invites = (
            await mongo
            .find("collaboration_invites", {"invitee_id": str(current_user.id), "status": "PENDING"})
            .sort("created_at", -1)
            .to_list(length=None)
        )
        return invites

    @staticmethod
    async def respond_to_collaboration_invite(
        invite_id: str, status: str, current_user
    ) -> dict:
        invite = await CooperationRepository.find_invite(
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
        await CooperationRepository.update_invite(
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
        await ActivityService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Accepted" if status == "ACCEPTED" else "Declined",
            "The recipient has officially registered their response to the pending editorial collaboration invitation",
        )
        logger.info("Collaboration invitation response processed")
        return {"message": "Ghi nhận trạng thái phản hồi lời mời cộng tác hoàn tất"}

    @staticmethod
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
    async def revoke_invite(invite_id: str, current_user) -> dict:
        invite = await CooperationRepository.find_invite(
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
        await CooperationRepository.delete_invite(
            {"_id": invite_id}
        )
        await ActivityService.log_activity(
            invite["document_id"],
            current_user.full_name,
            "Invitation revoked",
            "The active collaboration invitation token has been securely invalidated by the document owner",
        )
        return {"message": "Hủy bỏ và thu hồi lời mời tham gia cộng tác hoàn tất"}
