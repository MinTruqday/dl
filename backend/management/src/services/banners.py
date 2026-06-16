from datetime import datetime, timezone
from core.database import db_client
from loguru import logger
from uuid6 import uuid7

class BannerService:

    @staticmethod
    async def get_banners(active_only: bool = True, db=None) -> list:
        target_db = db or db_client.mongodb.get_default_database()
        query = {"is_active": True} if active_only else {}
        return await target_db["banners"].find(query).sort("priority", -1).to_list(length=20)

    @staticmethod
    async def create_banner(data: dict, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        banner = {
            "_id": str(uuid7()),
            "title": data.get("title"),
            "image_url": data.get("image_url"),
            "link_url": data.get("link_url"),
            "priority": data.get("priority", 0),
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        await target_db["banners"].insert_one(banner)
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return banner

    @staticmethod
    async def delete_banner(banner_id: str, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        await target_db["banners"].delete_one({"_id": banner_id})
        logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}