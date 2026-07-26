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

    await setup_indexes()

async def setup_indexes():
    try:
        db = database.mongodb[settings.COMPILATION_DB_NAME]
        await db["editor_suggestions"].create_index([("document_id", 1), ("status", 1), ("created_at", -1)])
        await db["editor_comments"].create_index([("document_id", 1), ("status", 1), ("created_at", -1)])
        await db["pomodoro_sessions"].create_index([("user_id", 1), ("created_at", -1)])
        await db["pomodoro_sessions"].create_index([("created_at", 1)], expireAfterSeconds=365 * 24 * 60 * 60)
        logger.info("MongoDB index initialization completed")
    except Exception:
        logger.exception("Failed to initialize MongoDB collection indexes")
        raise

async def close_db():
    if database.mongodb:
        database.mongodb.close()
        database.mongodb = None
    from src.core.infrastructure.redis import redis
    from src.core.infrastructure.http_client import http_client
    await redis.aclose()
    await http_client.aclose()
