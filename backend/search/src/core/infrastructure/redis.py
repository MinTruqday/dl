import redis.asyncio as aioredis
from loguru import logger
from src.core.infrastructure.configuration import settings

class RedisInfrastructure:
    def __init__(self):
        self._client: aioredis.Redis | None = None

    def get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                settings.REDIS_URI,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
            )
            logger.info("Search Redis connected")
        return self._client

    async def get(self, key: str) -> str | None:
        return await self.get_client().get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool | None:
        return await self.get_client().set(key, value, ex=ex)

    async def delete(self, *keys: str) -> int:
        return await self.get_client().delete(*keys)

    async def aclose(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Search Redis connection closed")

redis = RedisInfrastructure()
