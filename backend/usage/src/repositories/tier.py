from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any
from datetime import datetime, timezone

class TierRepository:
    @staticmethod
    async def get_user_tier(user_id: str) -> Optional[Dict[str, Any]]:
        return await mongo.find_one(collection="subscriptions", query={"user_id": user_id})

    @staticmethod
    async def create_or_update_tier(user_id: str, ai_tier: str, is_premium: bool, expires_at=None):
        now = datetime.now(timezone.utc)
        values = {
            "ai_tier": ai_tier,
            "is_premium": is_premium,
            "updated_at": now,
        }
        if expires_at is not None:
            values["expires_at"] = expires_at
        elif ai_tier == "BASIC":
            values["expires_at"] = None
        return await mongo.get_db()["subscriptions"].update_one(
            {"user_id": user_id},
            {"$set": values, "$setOnInsert": {"created_at": now}},
            upsert=True
        )
