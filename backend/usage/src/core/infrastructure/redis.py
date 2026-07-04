import json
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
            logger.exception(f"Lỗi lưu trữ dữ liệu (SET) vào Redis Cache với khóa {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def setex(self, key: str, expire: int, value: str):
        try:
            return await self.get_client().setex(key, expire, value)
        except Exception as e:
            logger.exception(f"Lỗi lưu trữ dữ liệu có thời hạn (SETEX) vào Redis Cache với khóa {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def get(self, key: str):
        try:
            return await self.get_client().get(key)
        except Exception as e:
            logger.exception(f"Lỗi lấy dữ liệu (GET) từ Redis Cache với khóa {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def delete(self, key: str):
        try:
            return await self.get_client().delete(key)
        except Exception as e:
            logger.exception(f"Lỗi xóa dữ liệu (DELETE) khỏi Redis Cache với khóa {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def sadd(self, key: str, member: str):
        try:
            return await self.get_client().sadd(key, member)
        except Exception as e:
            logger.exception(f"Lỗi thêm phần tử (SADD) vào set Redis Cache với khóa {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def sismember(self, key: str, member: str):
        try:
            return await self.get_client().sismember(key, member)
        except Exception as e:
            logger.exception(f"Lỗi kiểm tra phần tử (SISMEMBER) trong set Redis Cache với khóa {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def smembers(self, key: str):
        try:
            return await self.get_client().smembers(key)
        except Exception as e:
            logger.exception(f"Lỗi lấy danh sách phần tử (SMEMBERS) từ set Redis Cache với khóa {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def publish(self, channel: str, message: str):
        try:
            return await self.get_client().publish(channel, message)
        except Exception as e:
            logger.exception(f"Lỗi xuất bản tin nhắn (PUBLISH) lên kênh {channel} của Redis Cache")
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
            logger.exception(f"Lỗi thực thi pipeline (INCR/EXPIRE) trên Redis Cache với khóa {key}")
            raise Exception("Dịch vụ bộ đệm tạm thời không khả dụng")

    async def aclose(self):
        if self._client:
            await self._client.aclose()

redis = RedisAPIClient()
