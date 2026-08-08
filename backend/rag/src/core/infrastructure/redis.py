from redis.asyncio import Redis, from_url
from src.core.infrastructure.configuration import settings

class RedisInfrastructure:
    def __init__(self):
        self.client: Redis | None = None

    async def init_redis(self):
        self.client = from_url(settings.REDIS_URI, decode_responses=True)

    async def close_redis(self):
        if self.client:
            await self.client.close()

redis_client = RedisInfrastructure()
