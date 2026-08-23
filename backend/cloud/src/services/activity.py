from datetime import datetime, timezone
import uuid
from typing import List, Optional

from loguru import logger
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings
from src.schemas.storage import ItemActivityResponse


class ActivityService:
    @staticmethod
    async def log_activity(
        item_id: str,
        actor_id: str,
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        try:
            doc = {
                "_id": str(uuid.uuid4()),
                "item_id": item_id,
                "actor_id": actor_id,
                "action": action,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.now(timezone.utc),
            }
            await database.mongodb[settings.CLOUD_DB_NAME].storage_activities.insert_one(doc)
            return True
        except Exception as e:
            logger.error(f"Failed to log activity for item {item_id}: {e}")
            return False

    @staticmethod
    async def get_item_activities(item_id: str, limit: int = 50) -> List[ItemActivityResponse]:
        cursor = (
            database.mongodb[settings.CLOUD_DB_NAME]
            .storage_activities.find({"item_id": item_id})
            .sort([("timestamp", -1)])
            .limit(limit)
        )
        activities = await cursor.to_list(length=limit)

        results = []
        for a in activities:
            a["id"] = a.pop("_id")
            results.append(ItemActivityResponse(**a))
        return results
