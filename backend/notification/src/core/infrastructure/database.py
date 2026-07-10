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
                logger.info("RabbitMQ connection is stable")
                break
            else:
                raise Exception("MQ health check failed")
        except Exception as e:
            if i == max_retries - 1:
                logger.exception("RabbitMQ connection failed")
                raise e
            logger.exception("Retrying RabbitMQ connection")
            await asyncio.sleep(5)

    await setup_indexes()

async def setup_indexes():
    try:
        db = database.mongodb[settings.NOTIFICATION_DB_NAME]

        logger.info("MongoDB index creation completed")
    except Exception as e:
        logger.exception("MongoDB index creation failed")

async def close_db():
    if database.mongodb:
        database.mongodb.close()

