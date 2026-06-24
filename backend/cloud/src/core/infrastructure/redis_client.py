import json
import redis.asyncio as redis
from loguru import logger
from src.core.infrastructure.configuration import settings

class RedisAPIClient:
    def __init__(self):
        self.url = settings.REDIS_URI
        self._client = None

    def get_client(self):
        if self._client is None:
            self._client = redis.from_url(self.url, decode_responses=True)
        return self._client

    async def set(self, key: str, value: str):
        try:
            return await self.get_client().set(key, value)
        except Exception as e:
            logger.error(f"Redis Cache Server Error SET {key}: {e}")
            raise Exception("Cache service unavailable")

    async def setex(self, key: str, expire: int, value: str):
        try:
            return await self.get_client().setex(key, expire, value)
        except Exception as e:
            logger.error(f"Redis Cache Server Error SETEX {key}: {e}")
            raise Exception("Cache service unavailable")

    async def get(self, key: str):
        try:
            return await self.get_client().get(key)
        except Exception as e:
            logger.error(f"Redis Cache Server Error GET {key}: {e}")
            raise Exception("Cache service unavailable")

    async def delete(self, key: str):
        try:
            return await self.get_client().delete(key)
        except Exception as e:
            logger.error(f"Redis Cache Server Error DELETE {key}: {e}")
            raise Exception("Cache service unavailable")

    async def sadd(self, key: str, member: str):
        try:
            return await self.get_client().sadd(key, member)
        except Exception as e:
            raise Exception("Cache service unavailable")

    async def sismember(self, key: str, member: str):
        try:
            return await self.get_client().sismember(key, member)
        except Exception as e:
            raise Exception("Cache service unavailable")

    async def smembers(self, key: str):
        try:
            return await self.get_client().smembers(key)
        except Exception as e:
            raise Exception("Cache service unavailable")

    async def publish(self, channel: str, message: str):
        try:
            return await self.get_client().publish(channel, message)
        except Exception as e:
            raise Exception("Cache service unavailable")

    async def pipeline_incr_expire(self, key: str, expire: int):
        try:
            client = self.get_client()
            async with client.pipeline() as pipe:
                await pipe.incr(key)
                await pipe.expire(key, expire)
                res = await pipe.execute()
                return res
        except Exception as e:
            raise Exception("Cache service unavailable")

    async def aclose(self):
        if self._client:
            await self._client.aclose()

redis_client = RedisAPIClient()
