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
        db = database.mongodb[settings.CLOUD_DB_NAME]

        await db["storage_items"].create_index([("owner_id", 1), ("parent_id", 1), ("is_trashed", 1)], background=True)
        await db["storage_items"].create_index([("shared_with.user_id", 1), ("parent_id", 1), ("is_trashed", 1)], background=True)
        await db["storage_items"].create_index([("url", 1)], background=True)
        await db["storage_items"].create_index(
            [("share_token", 1)],
            unique=True,
            partialFilterExpression={"share_token": {"$type": "string"}},
            background=True,
        )
        await db["storage_items"].create_index([("target_id", 1)], background=True)
        await db["storage_items"].create_index([("owner_id", 1), ("is_trashed", 1), ("updated_at", -1)], background=True)
        await db["temp_chat_files"].create_index("expires_at", expireAfterSeconds=0)

        logger.info("MongoDB indexes successfully created and applied")
    except Exception:
        logger.exception("Failed to initialize MongoDB indexes")
        raise

async def close_db():
    if database.mongodb:
        database.mongodb.close()
        database.mongodb = None
    await redis.aclose()
