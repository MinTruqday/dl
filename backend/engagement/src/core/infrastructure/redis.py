from redis.asyncio import Redis, from_url
from src.core.infrastructure.configuration import settings

class RedisClient:
    def __init__(self):
        self._client: Redis = None

    def get_client(self) -> Redis:
        if self._client is None:
            self._client = from_url(settings.REDIS_URI, decode_responses=True)
        return self._client

    async def aclose(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

redis = RedisClient()
