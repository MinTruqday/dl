from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from bson import ObjectId
from loguru import logger
from uuid6 import uuid7

from src.core.infrastructure.database import database


from src.repositories.system import SystemRepository
from src.repositories.moderation import ModerationRepository

from src.core.dependency import CurrentUser

class TelemetryService:

    @staticmethod
    @log_logic_execution
    async def track_event(
        event_name: str,
        properties: Dict[str, Any],
        current_user: Optional[CurrentUser] = None,
    ):
        telemetry_event = {
            "_id": str(uuid7()),
            "event_name": event_name,
            "properties": properties,
            "user_id": str(current_user.id) if current_user else "anonymous",
            "timestamp": datetime.now(timezone.utc),
        }
        await SystemRepository.insert_telemetry(telemetry_event)
        logger.debug("Telemetry event recorded successfully")
        return {"status": "success"}

    @staticmethod
    @log_logic_execution
    async def get_activity_stats(days: int = 7):
        since = datetime.now(timezone.utc) - timedelta(days=days)
        pipeline = [
            {"$match": {"timestamp": {"$gte": since}}},
            {"$group": {"_id": "$event_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        cursor = SystemRepository.aggregate_telemetry(pipeline)
        return await cursor 

    @staticmethod
    @log_logic_execution
    async def record_metric(
        metric_name: str, value: float, current_user: Optional[CurrentUser] = None
    ):
        return await TelemetryService.track_event(
            "performance_metric", {"metric": metric_name, "value": value}, current_user
        )

    @staticmethod
    @log_logic_execution
    async def get_system_stats() -> dict:
        total_users = await UserRepository.count_documents({})
        total_documents = await SystemRepository.count_documents({})
        total_authors = await UserRepository.count_documents(
            {"role": "AUTHOR"}
        )
        return {
            "total_users": total_users,
            "total_documents": total_documents,
            "total_authors": total_authors,
            "timestamp": datetime.now(timezone.utc),
        }

    @staticmethod
    @log_logic_execution
    async def get_sys_health() -> dict:
        try:
            await mongo.get_db().command("ping")
            mongo_status = "healthy"
        except Exception:
            mongo_status = "unhealthy"
        return {
            "status": "online",
            "mongodb": mongo_status,
            "timestamp": datetime.now(timezone.utc),
        }

    @staticmethod
    @log_logic_execution
    async def get_activity_log(user_id: str) -> list:
        return (
            await ModerationRepository.find_moderator_activities({"actor_id": user_id})
            .sort("timestamp", -1)
            .execute()
        )
