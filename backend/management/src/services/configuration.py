from src.core.api_client import db_client
from datetime import datetime, timezone

from loguru import logger

from src.core.infrastructure.database import database


class ConfigurationService:

    @staticmethod
    async def get_settings(current_user) -> dict:
        user = await db["users"].find_one(
            {"_id": str(current_user.id)}, {"settings": 1}
        )
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
        user_id = str(current_user.id)
        user = await db_client.find_one("users", {"_id": user_id}, {"settings": 1})
        current_settings = user.get("settings", {}) if user else {}
        merged_settings = {**current_settings, **settings_data}
        await db["users"].update_one(
            {"_id": user_id},
            {
                "$set": {
                    "settings": merged_settings,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info("Cập nhật cấu hình thành công")
        return {"message": "Cập nhật cấu hình cá nhân thành công"}
