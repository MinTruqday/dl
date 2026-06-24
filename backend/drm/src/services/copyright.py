from datetime import datetime, timezone
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings
from src.repositories.copyright import CopyrightRepository
from loguru import logger

class CopyrightService:
    @staticmethod
    async def resolve_copyright_dispute(
        dispute_id: str, resolution: str, current_user
    ) -> dict:
        await CopyrightRepository.update_dispute(
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
        logger.info("Giải quyết tranh chấp bản quyền thành công")
        return {"message": "Đã giải quyết tranh chấp bản quyền"}
    
    @staticmethod
    async def update_drm_settings(document_id: str, disable_copy: bool, hide_from_search: bool, current_user) -> dict:
        db = database.mongodb.get_database(settings.SERVICE_DB_NAME)
        await db["document_drm_settings"].update_one(
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
