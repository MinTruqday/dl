import asyncio

from loguru import logger

from src.core.infrastructure.configuration import settings


class DatabaseInfrastructure:
    def __init__(self):
        self.mongodb = None


database = DatabaseInfrastructure()


async def init_db():
    mongo_uri = settings.MONGODB_URI

    if not mongo_uri:
        raise RuntimeError("MongoDB URI is required")

    from motor.motor_asyncio import AsyncIOMotorClient

    database.mongodb = AsyncIOMotorClient(mongo_uri)
    await database.mongodb.admin.command("ping")

    from src.core.infrastructure.mq import mq

    max_retries = 5
    for i in range(max_retries):
        try:
            if await mq.health_check():
                logger.info("RabbitMQ connection established")
                break
            raise RuntimeError("RabbitMQ health check failed")
        except Exception:
            if i == max_retries - 1:
                logger.exception("RabbitMQ connection failed after maximum retries")
                raise
            logger.warning("RabbitMQ connection failed, retrying")
            await asyncio.sleep(2)

    await setup_indexes()


async def setup_indexes():
    try:
        db = database.mongodb[settings.COLLECTION_DB_NAME]

        await db["collection_jobs"].create_index(
            [("status", 1), ("created_at", -1)], background=True
        )
        await db["collection_jobs"].create_index(
            [("source", 1), ("created_at", -1)], background=True
        )
        await db["collection_jobs"].create_index(
            [("created_at", -1)], expireAfterSeconds=30 * 24 * 60 * 60
        )
        logger.info("MongoDB indexes created")
    except Exception:
        logger.exception("MongoDB index initialization failed")
        raise


async def close_db():
    if database.mongodb:
        database.mongodb.close()
        database.mongodb = None
    from src.core.infrastructure.redis import redis
    from src.core.infrastructure.mq import mq

    await redis.aclose()
    await mq.aclose()
