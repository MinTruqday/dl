import os

import redis.asyncio as redis
from loguru import logger

from shared.infrastructure.config import settings


class RedisDeduplication:
    def __init__(self):
        url = settings.REDIS_URI
        self.r = redis.from_url(url, decode_responses=True)

    async def is_collected(self, key_type: str, value: str) -> bool:

        redis_key = f"DataCollection:dedup:{key_type}"
        return await self.r.sismember(redis_key, value)

    async def mark_collected(self, key_type: str, value: str):
        redis_key = f"DataCollection:dedup:{key_type}"
        await self.r.sadd(redis_key, value)
        logger.debug("Ghi nhận thu thập tài nguyên thành công")


dedup = RedisDeduplication()
