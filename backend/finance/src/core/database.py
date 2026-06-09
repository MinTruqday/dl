import os
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

class DatabaseClient:
    def __init__(self):
        self.mongodb = None
        self.redis = None

db_client = DatabaseClient()

async def connect_to_mongo():
    from src.core.config import settings
    db_client.mongodb = AsyncIOMotorClient(settings.MONGODB_URI)
    logger.info("Connected to MongoDB from Finance Service")

async def close_mongo_connection():
    if db_client.mongodb:
        db_client.mongodb.close()
        logger.info("Closed MongoDB connection")
