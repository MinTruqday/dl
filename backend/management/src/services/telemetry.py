from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from core.database import db_client
from core.repositories.base import RepositoryFactory
from loguru import logger
from uuid6 import uuid7

class TelemetryService:

    @staticmethod
    async def track_event(event_name: str, properties: Dict[str, Any], current_user: Optional[Any] = None, db=None) -> dict:
        telemetry_event = {
            "_id": str(uuid7()),
            "event_name": event_name,
            "properties": properties,
            "user_id": str(current_user.get("id")) if current_user else "anonymous",
            "timestamp": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("telemetry").insert_one(telemetry_event)
        logger.debug("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {"status": "success"}

    @staticmethod
    async def get_activity_stats(days: int = 7, db=None) -> list:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        pipeline = [
            {"$match": {"timestamp": {"$gte": since}}},
            {"$group": {"_id": "$event_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        cursor = RepositoryFactory.get("telemetry").aggregate(pipeline)
        return await cursor.to_list(length=100)

    @staticmethod
    async def log_performance_metric(metric_name: str, value: float, current_user: Optional[Any] = None, db=None) -> dict:
        return await TelemetryService.track_event("performance_metric", {"metric": metric_name, "value": value}, current_user)

    @staticmethod
    async def get_system_stats(db=None) -> dict:
        total_users = await RepositoryFactory.get("users").count_documents({})
        total_documents = await RepositoryFactory.get("documents").count_documents({})
        total_authors = await RepositoryFactory.get("users").count_documents({"role": "AUTHOR"})
        return {
            "total_users": total_users,
            "total_documents": total_documents,
            "total_authors": total_authors,
            "timestamp": datetime.now(timezone.utc),
        }

    @staticmethod
    async def get_sys_health(db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        try:
            await target_db.command("ping")
            mongo_status = "healthy"
        except Exception:
            mongo_status = "unhealthy"
        return {"status": "online", "mongodb": mongo_status, "timestamp": datetime.now(timezone.utc)}

    @staticmethod
    async def get_activity_log(user_id: str, db=None) -> list:
        return await RepositoryFactory.get("moderator_activity").find({"actor_id": user_id}).sort("timestamp", -1).to_list(length=100)