from core.database import db_client
from datetime import datetime
import uuid
from loguru import logger

class MarketingService:
    @staticmethod
    async def create_marketing_campaign(title: str, target: str, discount: int) -> dict:
        db = db_client.mongodb.get_default_database()
        campaign = {
            "_id": str(uuid.uuid4()),
            "title": title,
            "target_audience": target,
            "discount_percent": discount,
            "status": "active",
            "created_at": datetime.utcnow()
        }
        await db["marketing_campaigns"].insert_one(campaign)
        logger.info(f"Marketing: Campaign '{title}' created")
        return {"message": "Đã tạo chiến dịch marketing thành công."}

    @staticmethod
    async def get_banners() -> list:
        db = db_client.mongodb.get_default_database()
        return await db["banners"].find({"is_active": True}).to_list(length=20)

    @staticmethod
    async def create_banner(data: dict) -> dict:
        db = db_client.mongodb.get_default_database()
        banner = {
            "_id": str(uuid.uuid4()),
            "image_url": data["image_url"],
            "link": data.get("link"),
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        await db["banners"].insert_one(banner)
        logger.info(f"Marketing: Banner created")
        return {"message": "Đã tạo banner quảng cáo thành công."}

    @staticmethod
    async def update_banner(banner_id: str, data: dict) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["banners"].update_one({"_id": banner_id}, {"$set": {**data, "updated_at": datetime.utcnow()}})
        logger.info(f"Marketing: Banner {banner_id} updated")
        return {"message": "Đã cập nhật banner thành công."}

    @staticmethod
    async def delete_banner(banner_id: str) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["banners"].delete_one({"_id": banner_id})
        logger.info(f"Marketing: Banner {banner_id} deleted")
        return {"message": "Đã xóa banner thành công."}
