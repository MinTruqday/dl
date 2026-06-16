from datetime import datetime, timezone
from core.database import db_client
from loguru import logger

class SettingService:

    @staticmethod
    async def get_settings(current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        user = await target_db["users"].find_one({"_id": str(current_user.get("id"))}, {"settings": 1})
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
    async def update_settings(settings_data: dict, current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        user_id = str(current_user.get("id"))
        user = await target_db["users"].find_one({"_id": user_id}, {"settings": 1})
        current_settings = user.get("settings", {}) if user else {}
        merged_settings = {**current_settings, **settings_data}
        await target_db["users"].update_one(
            {"_id": user_id},
            {"$set": {"settings": merged_settings, "updated_at": datetime.now(timezone.utc)}},
        )
        logger.info("System configuration settings have been successfully updated by authenticated user")
        return {"message": "Personal system configuration settings have been successfully updated and saved"}