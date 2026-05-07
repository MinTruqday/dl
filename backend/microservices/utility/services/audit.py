from core.database import db_client
from datetime import datetime
from loguru import logger
class AuditService:
    @staticmethod
    async def get_audit_logs(limit: int = 50, offset: int = 0) -> list:
        db = db_client.mongodb.get_default_database()
        logs = await db["audit_logs"].find().sort("timestamp", -1).skip(offset).limit(limit).to_list(length=limit)
        return [
            {
                "id": str(l["_id"]) if "_id" in l else "",
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
            "timestamp": datetime.utcnow()
        })
        logger.info(f"Audit: {action} by {actor_id} on {target_id}")
