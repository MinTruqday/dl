import redis.asyncio as redis
import os
from loguru import logger

from core.config import settings

class RedisDeduplicator:
    def __init__(self):
        url = settings.REDIS_URI
        self.r = redis.from_url(url, decode_responses=True)

    async def is_collected(self, key_type: str, value: str) -> bool:
        
        redis_key = f"Collector:dedup:{key_type}"
        return await self.r.sismember(redis_key, value)

    async def mark_collected(self, key_type: str, value: str):
        redis_key = f"Collector:dedup:{key_type}"
        await self.r.sadd(redis_key, value)
        logger.debug(f"Đã đánh dấu {value} là đã thu thập trong {redis_key}")

dedup = RedisDeduplicator()
