from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from src.core.infrastructure.configuration import settings

class Database:
    client: AsyncIOMotorClient = None
    mongodb: AsyncIOMotorDatabase = None

database = Database()

async def init_db():
    database.client = AsyncIOMotorClient(settings.MONGODB_URI)
    database.mongodb = database.client[settings.ENGAGEMENT_DB_NAME]
    await database.client.admin.command("ping")
    await setup_indexes()

async def setup_indexes():
    db = database.mongodb
    await db["reading_history"].create_index(
        [("user_id", 1), ("document_id", 1)], unique=True
    )
    await db["reading_history"].create_index([("user_id", 1), ("last_read_at", -1)])
    await db["reading_lists"].create_index([("user_id", 1), ("updated_at", -1)])
    await db["highlights"].create_index(
        [("user_id", 1), ("document_id", 1), ("created_at", -1)]
    )
    await db["bookmark_folders"].create_index([("user_id", 1), ("created_at", -1)])
    await db["user_pins"].create_index(
        [("user_id", 1), ("document_id", 1)], unique=True
    )
    await db["user_content_profiles"].create_index([("updated_at", -1)])

async def close_db():
    if database.client is not None:
        database.client.close()

def get_db() -> AsyncIOMotorDatabase:
    return database.mongodb
