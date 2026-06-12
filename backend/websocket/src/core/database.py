from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from core.config import settings
from loguru import logger

class DatabaseClient:
    def __init__(self):
        self.mongodb = None
        self.redis = None

    async def connect(self):
        try:
            self.mongodb = AsyncIOMotorClient(settings.MONGODB_URI)
            self.redis = redis.from_url(settings.REDIS_URI, decode_responses=True)
            logger.info("Đã kết nối với hệ thống cơ sở dữ liệu và bộ nhớ đệm")
        except Exception as e:
            logger.error('Lỗi kết nối cơ sở dữ liệu')

    async def disconnect(self):
        if self.mongodb:
            self.mongodb.close()
        if self.redis:
            await self.redis.close()

db_client = DatabaseClient()
