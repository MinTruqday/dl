from shared.core.database import db_client
from datetime import datetime
import uuid
from loguru import logger
class BannerService:
    @staticmethod
    async def get_banners(active_only: bool = True) -> list:
        db = db_client.mongodb.get_default_database()
        query = {"is_active": True} if active_only else {}
        return await db["banners"].find(query).sort("priority", -1).to_list(length=20)
    @staticmethod
    async def create_banner(data: dict) -> dict:
        db = db_client.mongodb.get_default_database()
        banner = {
            "_id": str(uuid.uuid4()),
            "title": data.get("title"),
            "image_url": data.get("image_url"),
            "link_url": data.get("link_url"),
            "priority": data.get("priority", 0),
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        await db["banners"].insert_one(banner)
logger.info("Log message sanitized"))
        return banner
    @staticmethod
    async def delete_banner(banner_id: str) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["banners"].delete_one({"_id": banner_id})
logger.info("Log message sanitized"))
        return {"message": "Đã xóa banner thành công."}
