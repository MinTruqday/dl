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
        db = database.mongodb[settings.MANAGEMENT_DB_NAME]

        await db["reports"].create_index([("status", 1)], background=True)
        await db["reports"].create_index([("created_at", -1)], background=True)
        await db["audit_logs"].create_index([("timestamp", -1)], background=True)
        await db["audit_logs"].create_index([("actor_id", 1), ("timestamp", -1)], background=True)
        await db["telemetry"].create_index([("timestamp", -1)], background=True)
        await db["system_config"].create_index("key", unique=True)

        logger.info("MongoDB indexing initialized")
    except Exception:
        logger.exception("MongoDB indexing error")
        raise

async def close_db():
    if database.mongodb:
        database.mongodb.close()
        database.mongodb = None
    await redis.aclose()
