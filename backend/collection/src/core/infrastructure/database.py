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

    from src.core.infrastructure.mq import mq
    max_retries = 5
    for i in range(max_retries):
        try:
            if await mq.health_check():
                logger.info("RabbitMQ connection established successfully")
                break
            else:
                raise RuntimeError("RabbitMQ health check failed")
        except Exception as e:
            if i == max_retries - 1:
                logger.exception("RabbitMQ connection failed after maximum retries")
                raise e
            logger.exception("RabbitMQ connection failed, retrying...")
            await asyncio.sleep(5)

    await setup_indexes()

async def setup_indexes():
    try:
        db = database.mongodb[settings.COLLECTION_DB_NAME]

        await db["status_updates"].create_index([("created_at", -1)], background=True)
        await db["status_updates"].create_index([("user_id", 1)], background=True)
        await db["status_updates"].create_index([("is_shadowbanned", 1)], background=True)

        logger.info("MongoDB indexes created successfully")
    except Exception as e:
        logger.exception("MongoDB index initialization failed")

async def close_db():
    if database.mongodb:
        database.mongodb.close()

