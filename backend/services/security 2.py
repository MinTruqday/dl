from shared.core.database import db_client
from datetime import datetime
from loguru import logger

class SecurityService:
    @staticmethod
    async def get_security_config() -> dict:
        db = db_client.mongodb.get_default_database()
        config = await db["system_config"].find_one({"key": "security_settings"})
        return config.get("value", {}) if config else {
            "mfa_required": False,
            "session_timeout_minutes": 60,
            "ip_whitelist_enabled": False
        }

    @staticmethod
    async def update_security_config(data: dict) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["system_config"].update_one(
            {"key": "security_settings"},
            {"$set": {"value": data, "updated_at": datetime.utcnow()}},
            upsert=True
        )
logger.info("Log message sanitized"))
        return {"message": "Đã cập nhật cấu hình bảo mật hệ thống."}
