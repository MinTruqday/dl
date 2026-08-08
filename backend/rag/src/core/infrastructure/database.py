from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from src.core.infrastructure.configuration import settings

class Database:
    client: AsyncIOMotorClient = None
    mongodb: AsyncIOMotorDatabase = None

database = Database()

async def init_db():
    database.client = AsyncIOMotorClient(settings.MONGODB_URI)
    database.mongodb = database.client[settings.RAG_DB_NAME]

async def close_db():
    if database.client is not None:
        database.client.close()

def get_db() -> AsyncIOMotorDatabase:
    return database.mongodb
