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
                raise Exception("MQ health check failed")
        except Exception as e:
            if i == max_retries - 1:
                logger.exception("RabbitMQ connection error")
                raise e
            logger.warning("Attempting to reconnect to RabbitMQ")
            await asyncio.sleep(5)

    await setup_indexes()

async def setup_indexes():
    try:
        db = database.mongodb[settings.CONTENT_DB_NAME]

        await db["documents"].create_index([("title", "text"), ("description", "text"), ("author", "text")], background=True)
        await db["documents"].create_index([("creator_id", 1)], background=True)
        await db["documents"].create_index([("status", 1), ("is_deleted", 1), ("created_at", -1)], background=True)
        await db["documents"].create_index([("status", 1), ("is_deleted", 1), ("views", -1)], background=True)
        await db["documents"].create_index([("status", 1), ("is_deleted", 1), ("categories", 1), ("created_at", -1)], background=True)
        await db["documents"].create_index([("status", 1), ("is_deleted", 1), ("tags", 1), ("created_at", -1)], background=True)
        await db["documents"].create_index([("slug", 1)], unique=True, background=True)

        await db["comments"].create_index([("item_id", 1), ("item_type", 1)], background=True)
        await db["comments"].create_index([("path", 1)], background=True)

        await db["editor_comments"].create_index([("document_id", 1), ("block_id", 1)], background=True)

        await db["document_versions"].create_index([("document_id", 1), ("created_at", -1)], background=True)

        logger.info("MongoDB indexing initialized successfully")
    except Exception as e:
        logger.exception("MongoDB indexing error")

async def close_db():
    if database.mongodb:
        database.mongodb.close()

