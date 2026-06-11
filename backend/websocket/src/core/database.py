from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from src.config import settings
from loguru import logger

class DatabaseClient:
    def __init__(self):
        self.mongodb = None
        self.redis = None

    async def connect(self):
        try:
            self.mongodb = AsyncIOMotorClient(settings.MONGODB_URI)
            self.redis = redis.from_url(settings.REDIS_URI, decode_responses=True)
            logger.info("Connected to MongoDB and Redis")
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")

    async def disconnect(self):
        if self.mongodb:
            self.mongodb.close()
        if self.redis:
            await self.redis.close()

db_client = DatabaseClient()
