from core.database import db_client
from datetime import datetime, timezone
import uuid
from uuid6 import uuid7
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
            "_id": str(uuid7()),
            "title": data.get("title"),
            "image_url": data.get("image_url"),
            "link_url": data.get("link_url"),
            "priority": data.get("priority", 0),
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
        await db["banners"].insert_one(banner)
        logger.info(f"Marketing: New banner '{banner.get('title')}' created.")
        return banner

    @staticmethod
    async def delete_banner(banner_id: str) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["banners"].delete_one({"_id": banner_id})
        logger.info(f"Marketing: Banner {banner_id} deleted.")
        return {"message": "Xoá biểu ngữ thành công."}
