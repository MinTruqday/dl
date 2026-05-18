from core.database import db_client
from datetime import datetime, timezone
from loguru import logger

class AuditService:
    @staticmethod
    async def get_audit_logs(limit: int = 50, cursor: str = None) -> list:
        db = db_client.mongodb.get_default_database()
        query = {}
        if cursor:
            query["timestamp"] = {"$lt": datetime.fromisoformat(cursor.replace('Z', '+00:00'))}
        logs = await db["audit_logs"].find(query).sort("timestamp", -1).limit(limit).to_list(length=limit)
        return [
            {
                "_id": str(l["_id"]) if "_id" in l else "",
                "action": l.get("action"),
                "actor_id": l.get("actor_id"),
                "target_id": l.get("target_id") or l.get("target_user_id") or l.get("document_id"),
                "timestamp": l["timestamp"].isoformat() if isinstance(l.get("timestamp"), datetime) else l.get("timestamp"),
            }
            for l in logs
        ]

    @staticmethod
    async def log_action(action: str, actor_id: str, target_id: str = None, details: dict = None):
        db = db_client.mongodb.get_default_database()
        await db["audit_logs"].insert_one({
            "action": action,
            "actor_id": actor_id,
            "target_id": target_id,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc)
        })
        logger.info(f"Audit: Action '{action}' by '{actor_id}' on '{target_id}' recorded.")
