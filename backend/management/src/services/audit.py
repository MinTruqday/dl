from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
from datetime import datetime, timezone

from loguru import logger

from src.core.infrastructure.database import database

class AuditService:

    @staticmethod
    @log_logic_execution
    async def get_audit_logs(limit: int = 50, cursor: str = None) -> list:
        query = {}
        if cursor:
            query["timestamp"] = {
                "$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            }
        logs = (
            await database.mongodb["audit_logs"]
            .find(query)
            .sort("timestamp", -1)
            .limit(limit)
            .execute()
        )
        return [
            {
                "_id": str(l["_id"]) if "_id" in l else "",
                "action": l.get("action"),
                "actor_id": l.get("actor_id"),
                "target_id": l.get("target_id")
                or l.get("target_user_id")
                or l.get("document_id"),
                "timestamp": (
                    l["timestamp"].isoformat()
                    if isinstance(l.get("timestamp"), datetime)
                    else l.get("timestamp")
                ),
            }
            for l in logs
        ]

    @staticmethod
    @log_logic_execution
    async def log_action(
        action: str, actor_id: str, target_id: str = None, details: dict = None
    ):
        await mongo.insert_one("audit_logs", 
            {
                "action": action,
                "actor_id": actor_id,
                "target_id": target_id,
                "details": details or {},
                "timestamp": datetime.now(timezone.utc),
            }
        )
        logger.info("Ghi nhận thao tác thành công")
