from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from src.core.infrastructure.configuration import settings

class Database:
    client: AsyncIOMotorClient = None
    mongodb: AsyncIOMotorDatabase = None

database = Database()

async def init_db():
    database.client = AsyncIOMotorClient(settings.MONGODB_URI)
    database.mongodb = database.client[settings.RAG_DB_NAME]
    await database.mongodb.retrieval_audit.create_index([("requester_id", 1), ("created_at", -1)])
    await database.mongodb.retrieval_audit.create_index([("document_ids", 1), ("created_at", -1)])

async def close_db():
    if database.client is not None:
        database.client.close()

def get_db() -> AsyncIOMotorDatabase:
    return database.mongodb
