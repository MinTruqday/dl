import httpx
import json
from typing import Optional, Dict, Any
from src.core.infrastructure.redis import redis
from src.core.infrastructure.configuration import settings
from loguru import logger

class ProfileRepository:
    @classmethod
    async def get_profile(cls, user_id: str) -> Optional[Dict[str, Any]]:
        cache_key = f"profile:{user_id}"
        try:
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            logger.exception("Failed to read cached user profile")

        async with httpx.AsyncClient() as client:
            try:
                base = settings.HUMANITY_URL
                headers = {"X-Internal-Token": settings.SECRET_KEY}
                resp = await client.get(f"{base}/nguoi-dung/{user_id}", headers=headers, timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json().get("data")
                    if data:
                        try:
                            await redis.setex(cache_key, 300, json.dumps(data))
                        except Exception:
                            logger.exception("Failed to cache user profile")
                        return data
            except Exception:
                logger.exception("HTTP request failed while fetching user profile information")
        return None
