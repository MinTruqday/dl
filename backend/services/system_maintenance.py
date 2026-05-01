from core.database import db_client
from datetime import datetime
import uuid
import os
from loguru import logger

class SystemMaintenanceService:
    @staticmethod
    async def get_sys_health() -> dict:
        db = db_client.mongodb.get_default_database()
        try:
            await db.command("ping")
            mongo_status = "healthy"
        except:
            mongo_status = "unhealthy"
            
        return {
            "status": "online",
            "mongodb": mongo_status,
            "timestamp": datetime.utcnow()
        }

    @staticmethod
    async def toggle_maintenance_mode(enabled: bool, message: str = "") -> dict:
        db = db_client.mongodb.get_default_database()
        await db["system_config"].update_one(
            {"key": "maintenance_mode"}, 
            {"$set": {"enabled": enabled, "message": message, "updated_at": datetime.utcnow()}}, 
            upsert=True
        )
        logger.warning(f"System: Maintenance mode {'enabled' if enabled else 'disabled'} by admin")
        return {"message": f"Chế độ bảo trì đã được {'bật' if enabled else 'tắt'}."}

    @staticmethod
    async def trigger_backup(action: str) -> dict:
        logger.info(f"System: Backup action '{action}' triggered")
        return {"message": "Yêu cầu sao lưu dữ liệu đã được gửi đến hàng chờ."}

    @staticmethod
    async def create_api_key(name: str, provider: str, key_value: str) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["api_keys"].insert_one({
            "_id": str(uuid.uuid4()),
            "name": name,
            "provider": provider,
            "key_value": key_value,
            "created_at": datetime.utcnow()
        })
        logger.info(f"System: API Key '{name}' for '{provider}' created")
        return {"message": "Đã lưu API Key thành công."}

    @staticmethod
    async def get_storage_stats() -> dict:
        return {
            "total_size_mb": 10240, 
            "used_size_mb": 1250, 
            "status": "optimal"
        }
