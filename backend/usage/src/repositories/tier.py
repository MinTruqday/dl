from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any

class TierRepository:
    @staticmethod
    async def get_user_tier(user_id: str) -> Optional[Dict[str, Any]]:
        return await mongo.find_one(collection="subscriptions", query={"user_id": user_id})

    @staticmethod
    async def create_or_update_tier(user_id: str, ai_tier: str, is_premium: bool):
        return await mongo.get_db()["subscriptions"].update_one(
            {"user_id": user_id},
            {"$set": {"ai_tier": ai_tier, "is_premium": is_premium}},
            upsert=True
        )
