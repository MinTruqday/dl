from src.core.infrastructure.mongo import mongo
from typing import List, Dict, Any

class AuditService:
    @staticmethod
    async def get_moderator_activity_log(user_id: str) -> List[Dict[str, Any]]:
        logs = await mongo.find(collection="audit_logs", query={"actor_id": user_id}).sort("timestamp", -1).limit(50).execute()
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs
