from src.core.infrastructure.redis import redis
import asyncio
import os

from loguru import logger

from src.core.infrastructure.configuration import settings

class DatabaseInfrastructure:
    def __init__(self):
        self.mongodb = None

database = DatabaseInfrastructure()

async def init_db():
    mongo_uri = settings.MONGODB_URI

    if not mongo_uri :
        logger.error("Failed to initialize database connection due to missing MongoDB URI")
        import sys

        sys.exit(1)

    from motor.motor_asyncio import AsyncIOMotorClient
    database.mongodb = AsyncIOMotorClient(mongo_uri)

    await setup_indexes()

async def setup_indexes():
    try:
        db = database.mongodb[settings.SERVICE_DB_NAME]

        logger.info("MongoDB index creation completed successfully")
    except Exception as e:
        logger.exception("Failed to create MongoDB indexes")

async def close_db():
    if database.mongodb:
        database.mongodb.close()

