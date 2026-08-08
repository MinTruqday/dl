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
        creator_id = doc.get("creator_id")
        coauthors = doc.get("coauthors", [])
        roles = doc.get("coauthor_roles", {})
        all_user_ids = list(set([creator_id] + coauthors))
        collaborators = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for uid in all_user_ids:
                if not uid:
                    continue
                try:
                    resp = await client.get(
                        f"{settings.HUMANITY_URL}/nguoi-dung/{uid}",
                        headers={"X-Internal-Token": settings.SECRET_KEY},
                    )
                    if resp.status_code == 200:
                        user_info = resp.json().get("data", {})
                        is_owner = uid == creator_id
                        assigned_role = roles.get(uid, "editor")
                        collaborators.append(
                            {
                                "user_id": uid,
                                "email": user_info.get("email"),
                                "full_name": user_info.get("full_name"),
                                "role": "owner" if is_owner else assigned_role,
                                "is_owner": is_owner,
                            }
                        )
                except Exception:
                    logger.warning("Failed to fetch collaborator profile information")
        return collaborators

    @staticmethod
    @log_logic_execution
    async def remove_collaborator(
        document_id: str, collaborator_id: str, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Hệ thống không tìm thấy tài liệu yêu cầu hoặc bạn không có quyền truy cập",
            )
        if collaborator_id == str(current_user.id):
            raise HTTPException(
                status_code=400,
                detail="Thao tác không hợp lệ: Không thể xóa quyền truy cập của chủ sở hữu tài liệu",
            )
        await DocumentRepository.update_one(
            {"_id": document_id},
            {
                "$pull": {"coauthors": collaborator_id},
                "$unset": {f"coauthor_roles.{collaborator_id}": ""},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        await ActivityService.log_activity(
            document_id,
            current_user.full_name,
            "Remove collaborator",
            "Editorial and collaborative rights have been revoked for the targeted user",
        )
        logger.info("Collaboration privileges revoked")
        return {"message": "Xóa quyền truy cập của cộng tác viên khỏi tài liệu hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def update_collaborator_role(
        document_id: str, collaborator_id: str, role: str, current_user
    ) -> dict:
        if role not in ["editor", "commenter", "viewer"]:
            raise HTTPException(status_code=400, detail="Phân quyền truy cập cung cấp không hợp lệ")
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc bạn không phải là chủ sở hữu",
            )
        if collaborator_id == str(current_user.id):
            raise HTTPException(
                status_code=400,
                detail="Không thể điều chỉnh phân quyền của chính chủ sở hữu tài liệu",
            )
        coauthors = doc.get("coauthors", [])
        if collaborator_id not in coauthors:
            raise HTTPException(
                status_code=404, detail="Người dùng không nằm trong danh sách cộng tác viên của tài liệu"
            )
        await DocumentRepository.update_one(
            {"_id": document_id},
            {
                "$set": {
                    f"coauthor_roles.{collaborator_id}": role,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        await ActivityService.log_activity(
            document_id,
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
