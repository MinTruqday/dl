from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
from datetime import datetime, timezone
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings
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
        document = await database.mongodb["doclib_content"]["documents"].find_one(
            {"_id": document_id},
            {"creator_id": 1, "coauthors": 1},
        )
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
        user_id = str(current_user.id)
        is_owner = document.get("creator_id") == user_id
        is_coauthor = user_id in document.get("coauthors", [])
        from src.core.dependency import Role
        if getattr(current_user.role, "value", current_user.role) != Role.ADMIN.value and not is_owner and not is_coauthor:
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
