from datetime import datetime, timezone
from core.database import db_client
from loguru import logger

class SettingService:
    @staticmethod
    async def get_settings(current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)}, {"settings": 1})
        defaults = {
            "appearance": "light",
            "fontSize": "medium",
            "notifications": True,
            "privacyProfile": "public",
            "privacyActivity": True,
            "twoFactor": False,
            "notifyCommunity": {"email": True, "inapp": True},
            "notifyFinance": {"email": True, "inapp": True},
            "notifyUpdates": {"email": False, "inapp": True},
            "notifyNewsletter": {"email": True, "inapp": False},
        }
        if user and "settings" in user:
            defaults.update(user["settings"])
        return defaults

    @staticmethod
    async def update_settings(settings_data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["users"].update_one(
            {"_id": str(current_user.id)},
            {"$set": {"settings": settings_data, "updated_at": datetime.now(timezone.utc)}}
        )
logger.info("Log message sanitized"))
        return {"message": "Đã lưu cài đặt."}
