from datetime import datetime, timezone
import httpx
from fastapi import HTTPException
from loguru import logger
from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.configuration import settings
from src.repositories.cooperation import CooperationRepository, DocumentRepository
from src.services.activity import ActivityService

class MemberService:
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
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        invitations = await CooperationRepository.find_invites(
            {"document_id": document_id, "status": "ACCEPTED"}
        )
        collaborators = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for invitation in invitations:
                user_id = invitation.get("invitee_id")
                try:
                    resp = await client.get(
                        f"{settings.HUMANITY_URL}/nguoi-dung/{user_id}",
                        headers={"X-Internal-Token": settings.SECRET_KEY},
                    )
                    if resp.status_code == 200:
                        user_info = resp.json().get("data", {})
                        collaboration_id = str(invitation["_id"])
                        collaborators.append(
                            {
                                "_id": collaboration_id,
                                "id": collaboration_id,
                                "collaboration_id": collaboration_id,
                                "user_id": user_id,
                                "email": user_info.get("email", ""),
                                "full_name": user_info.get("full_name", "User"),
                                "role": invitation.get("role", "editor"),
                            }
                        )
                except Exception:
                    logger.warning("Failed to fetch collaborator profile information")
        return collaborators

    @staticmethod
    @log_logic_execution
    async def remove_collaborator(
        collaboration_id: str, current_user
    ) -> dict:
        invitation = await CooperationRepository.find_invite(
            {"_id": collaboration_id}
        )
        if not invitation:
            raise HTTPException(
                status_code=404,
                detail="Hệ thống gặp sự cố khi tải cấu hình môi trường cộng tác",
            )
        doc = await DocumentRepository.find_one(
            {
                "_id": invitation["document_id"],
                "creator_id": str(current_user.id),
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Hệ thống không tìm thấy tài liệu yêu cầu hoặc bạn không có quyền truy cập",
            )
        await DocumentRepository.update_one(
            {"_id": invitation["document_id"]},
            {
                "$pull": {"coauthors": invitation["invitee_id"]},
                "$unset": {f"coauthor_roles.{invitation['invitee_id']}": ""},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        await CooperationRepository.delete_invite({"_id": collaboration_id})
        await ActivityService.log_activity(
            invitation["document_id"],
            current_user.full_name,
            "Remove collaborator",
            "Editorial and collaborative rights have been revoked for the targeted user",
        )
        logger.info("Collaboration privileges revoked")
        return {"message": "Xóa quyền truy cập của cộng tác viên khỏi tài liệu hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def update_collaborator_role(
        collaboration_id: str, role: str, current_user
    ) -> dict:
        if role not in ["editor", "commenter", "viewer"]:
            raise HTTPException(status_code=400, detail="Phân quyền truy cập cung cấp không hợp lệ")
        invitation = await CooperationRepository.find_invite({"_id": collaboration_id})
        if not invitation:
            raise HTTPException(status_code=404, detail="Lỗi tải cấu hình môi trường cộng tác")
        doc = await DocumentRepository.find_one(
            {
                "_id": invitation["document_id"],
                "creator_id": str(current_user.id),
            }
        )
        if not doc:
            raise HTTPException(
                status_code=403,
                detail="Không có quyền quản lý người tham gia",
            )
        await CooperationRepository.update_invite(
            {"_id": collaboration_id},
            {"$set": {"role": role}},
        )
        await ActivityService.log_activity(
            invitation["document_id"],
            current_user.full_name,
            f"Update role to {role}",
            "Access permissions for the designated collaborator have been updated",
        )
        return {"message": "Cập nhật phân quyền cộng tác viên hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def transfer_ownership(
        document_id: str, new_owner_id: str, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc bạn không phải là chủ sở hữu",
            )
        if new_owner_id == str(current_user.id):
            raise HTTPException(
                status_code=400,
                detail="Không thể chuyển quyền sở hữu cho chính bản thân bạn",
            )
        coauthors = doc.get("coauthors", [])
        if new_owner_id not in coauthors:
            raise HTTPException(
                status_code=400,
                detail="Người nhận quyền sở hữu phải là một trong các cộng tác viên hiện tại",
            )
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.HUMANITY_URL}/nguoi-dung/{new_owner_id}",
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
        except Exception:
            logger.exception("Failed to retrieve ownership transfer target")
            raise HTTPException(
                status_code=503,
                detail="Dịch vụ hồ sơ người dùng tạm thời không khả dụng",
            )
        if response.status_code != 200 or not response.json().get("data"):
            raise HTTPException(
                status_code=404,
                detail="Hệ thống không tìm thấy tài khoản để chuyển quyền sở hữu",
            )
        new_coauthors = [uid for uid in coauthors if uid != new_owner_id]
        new_coauthors.append(str(current_user.id))
        roles = doc.get("coauthor_roles", {})
        if new_owner_id in roles:
            del roles[new_owner_id]
        roles[str(current_user.id)] = "editor"
        await DocumentRepository.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "creator_id": new_owner_id,
                    "coauthors": new_coauthors,
                    "coauthor_roles": roles,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        await ActivityService.log_activity(
            document_id,
            current_user.full_name,
            "Transfer ownership",
            "Primary administrative and document ownership rights have been transferred to the designated collaborator",
        )
        return {"message": "Chuyển giao quyền sở hữu tài liệu hoàn tất"}
