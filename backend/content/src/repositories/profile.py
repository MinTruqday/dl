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
            if cached: return json.loads(cached)
        except: pass

        async with httpx.AsyncClient() as client:
            try:
                base = settings.HUMANITY_URL
                headers = {"X-Internal-Token": settings.SECRET_KEY}
                resp = await client.get(f"{base}/nguoi-dung/{user_id}", headers=headers, timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json().get("data")
                    if data:
                        try: await redis.setex(cache_key, 300, json.dumps(data))
                        except: pass
                        return data
            except Exception as e:
                logger.exception("Lỗi HTTP khi lấy thông tin hồ sơ")
        return None

    @classmethod
    async def update_profile(cls, user_id: str, update_query: dict):
        async with httpx.AsyncClient() as client:
            try:
                base = settings.HUMANITY_URL
                headers = {"X-Internal-Token": settings.SECRET_KEY}
                resp = await client.put(f"{base}/nguoi-dung/{user_id}", json=update_query, headers=headers, timeout=5.0)
                if resp.status_code == 200:
                    try: await redis.delete(f"profile:{user_id}")
                    except: pass
            except Exception as e:
                logger.exception("Lỗi HTTP khi cập nhật thông tin hồ sơ")
