from src.core.infrastructure.redis import redis
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

    await database.mongodb.admin.command("ping")
    await setup_indexes()

async def setup_indexes():
    try:
        db = database.mongodb[settings.USAGE_DB_NAME]

        await db["subscriptions"].create_index("user_id", unique=True)
        await db["subscriptions"].create_index("expires_at")
        await db["quota_configs"].create_index("updated_at")

        logger.info("MongoDB indexes created and applied")
    except Exception:
        logger.exception("Failed to initialize MongoDB indexes")
        raise

async def close_db():
    if database.mongodb:
        database.mongodb.close()
        database.mongodb = None
    await redis.aclose()
