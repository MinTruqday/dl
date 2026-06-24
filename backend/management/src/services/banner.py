from src.core.api_client import db_client
import uuid
from datetime import datetime, timezone

from loguru import logger
from uuid6 import uuid7

from src.core.infrastructure.database import database


class BannerService:

    @staticmethod
    async def get_banners(active_only: bool = True) -> list:
        query = {"is_active": True} if active_only else {}
        return await db_client.find(collection="banners", query=query, sort=[("priority", -1)], limit=20)

    @staticmethod
    async def create_banner(data: dict) -> dict:
        banner = {
            "_id": str(uuid7()),
            "title": data.get("title"),
            "image_url": data.get("image_url"),
            "link_url": data.get("link_url"),
            "priority": data.get("priority", 0),
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        await db_client.insert_one(collection="banners", document=banner)
        logger.info("Tạo banner quảng cáo thành công")
        return banner

    @staticmethod
    async def delete_banner(banner_id: str) -> dict:
        await db_client.delete_one(collection="banners", filter={"_id": banner_id})
        logger.info("Xóa vĩnh viễn banner quảng cáo thành công")
        return {"message": "Xóa vĩnh viễn banner quảng cáo thành công"}
