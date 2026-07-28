import redis.asyncio as aioredis
from loguru import logger
from src.core.infrastructure.configuration import settings

class RedisAPIClient:
    def __init__(self):
        self.url = settings.REDIS_URI
        self._client = None

    def get_client(self):
        if self._client is None:
            self._client = aioredis.from_url(self.url, decode_responses=True)
        return self._client

    async def set(self, key: str, value: str):
        try:
            return await self.get_client().set(key, value)
        except Exception as e:
            logger.exception(f"Failed to execute SET operation on Redis Cache for key {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def setex(self, key: str, expire: int, value: str):
        try:
            return await self.get_client().setex(key, expire, value)
        except Exception as e:
            logger.exception(f"Failed to execute SETEX operation on Redis Cache for key {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def get(self, key: str):
        try:
            return await self.get_client().get(key)
        except Exception as e:
            logger.exception(f"Failed to execute GET operation on Redis Cache for key {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def delete(self, key: str):
        try:
            return await self.get_client().delete(key)
        except Exception as e:
            logger.exception(f"Failed to execute DELETE operation on Redis Cache for key {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def incr(self, key: str):
        try:
            return await self.get_client().incr(key)
        except Exception:
            logger.exception(f"Failed to execute INCR operation on Redis Cache for key {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def incrby(self, key: str, amount: int):
        try:
            return await self.get_client().incrby(key, amount)
        except Exception:
            logger.exception(f"Failed to execute INCRBY operation on Redis Cache for key {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def expire(self, key: str, seconds: int):
        try:
            return await self.get_client().expire(key, seconds)
        except Exception:
            logger.exception(f"Failed to execute EXPIRE operation on Redis Cache for key {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def ping(self):
        return await self.get_client().ping()

    async def sadd(self, key: str, member: str):
        try:
            return await self.get_client().sadd(key, member)
        except Exception:
            logger.exception(f"Failed to execute SADD operation on Redis Cache for key {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def sismember(self, key: str, member: str):
        try:
            return await self.get_client().sismember(key, member)
        except Exception as e:
            logger.exception(f"Failed to execute SISMEMBER operation on Redis Cache for key {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def smembers(self, key: str):
        try:
            return await self.get_client().smembers(key)
        except Exception as e:
            logger.exception(f"Failed to execute SMEMBERS operation on Redis Cache for key {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def publish(self, channel: str, message: str):
        try:
            return await self.get_client().publish(channel, message)
        except Exception as e:
            logger.exception(f"Failed to execute PUBLISH operation to Redis channel {channel}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def pipeline_incr_expire(self, key: str, expire: int):
        try:
            client = self.get_client()
            async with client.pipeline() as pipe:
                await pipe.incr(key)
                await pipe.expire(key, expire)
                res = await pipe.execute()
                return res
        except Exception as e:
            logger.exception(f"Failed to execute atomic INCR/EXPIRE pipeline on Redis Cache for key {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def reserve_below_limit(self, key: str, limit: int, expire: int):
        script = """
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
local limit = tonumber(ARGV[1])
if current >= limit then
    return -1
end
local updated = redis.call('INCR', KEYS[1])
if updated == 1 or redis.call('TTL', KEYS[1]) < 0 then
    redis.call('EXPIRE', KEYS[1], ARGV[2])
end
return updated
"""
        try:
            return await self.get_client().eval(script, 1, key, limit, expire)
        except Exception:
            logger.exception(f"Failed to reserve quota atomically for key {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def aclose(self):
        if self._client:
            await self._client.aclose()
            self._client = None

redis = RedisAPIClient()
