from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as aioredis

class DatabaseClient:
    def __init__(self):
        self.mongodb = None
        self.redis = None

db_client = DatabaseClient()

async def connect_to_db():
    from src.core.config import settings
    db_client.mongodb = AsyncIOMotorClient(settings.MONGODB_URI)
    logger.info("Authentication Service: Connected to MongoDB")
    try:
        db_client.redis = await aioredis.from_url(settings.REDIS_URI, decode_responses=True)
        logger.info("Authentication Service: Connected to Redis")
    except Exception as e:
        logger.warning(f"Authentication Service: Redis connection failed: {e}")
        db_client.redis = None

async def close_db():
    if db_client.mongodb:
        db_client.mongodb.close()
        logger.info("Authentication Service: MongoDB connection closed")
    if db_client.redis:
        await db_client.redis.close()
