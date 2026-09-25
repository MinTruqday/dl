import uuid
from datetime import datetime, timezone
from typing import List, Optional

from loguru import logger

from src.repositories.storage import activity_repository
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
            await activity_repository.insert(doc)
            return True
        except Exception as e:
            logger.error(f"Failed to log activity for item {item_id}: {e}")
            return False

    @staticmethod
    async def get_item_activities(item_id: str, limit: int = 50) -> List[ItemActivityResponse]:
        activities = await activity_repository.list_for_item(item_id, limit)

        results = []
        for a in activities:
            a["id"] = a.pop("_id")
            results.append(ItemActivityResponse(**a))
        return results
