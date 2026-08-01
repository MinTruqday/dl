from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
from datetime import datetime, timezone
from src.services.content_client import ContentClient
from src.repositories.copyright import CopyrightRepository
from loguru import logger
from fastapi import HTTPException

class CopyrightService:
    @staticmethod
    @log_logic_execution
    async def resolve_copyright_dispute(
        dispute_id: str, resolution: str, current_user
    ) -> dict:
        result = await CopyrightRepository.update_dispute(
            {"_id": dispute_id},
            {
                "$set": {
                    "status": "resolved",
                    "resolution": resolution,
                    "resolved_by": str(current_user.id),
                    "resolved_at": datetime.now(timezone.utc),
                }
            },
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy tranh chấp bản quyền")
        logger.info("Copyright dispute resolved")
        return {"message": "Đã giải quyết tranh chấp bản quyền"}
    
    @staticmethod
    @log_logic_execution
    async def update_drm_settings(document_id: str, disable_copy: bool, hide_from_search: bool, current_user) -> dict:
        user_id = str(current_user.id)
        from src.core.dependency import Role
        is_admin = getattr(current_user.role, "value", current_user.role) == Role.ADMIN.value
        document = await ContentClient.get_accessible(document_id, user_id, is_admin, edit=True)
        if not document:
            raise HTTPException(status_code=403, detail="Bạn không có quyền cấu hình DRM cho tài liệu này")
        await mongo.update_one("document_drm_settings", 
            {"document_id": document_id},
            {
                "$set": {
                    "disable_copy": disable_copy,
                    "hide_from_search": hide_from_search,
                    "updated_by": str(current_user.id),
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        return {"document_id": document_id, "disable_copy": disable_copy, "hide_from_search": hide_from_search}
