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
        logger.error("Lỗi khởi tạo do thiếu kết nối MongoDB")
        import sys

        sys.exit(1)

    from motor.motor_asyncio import AsyncIOMotorClient
    database.mongodb = AsyncIOMotorClient(mongo_uri)

    await setup_indexes()

async def setup_indexes():
    try:
        db = database.mongodb[settings.SERVICE_DB_NAME]

        await db["conversations"].create_index([("participants", 1), ("updated_at", -1)], background=True)

        await db["messages"].create_index([("sender_id", 1), ("receiver_id", 1), ("created_at", -1)], background=True)
        await db["messages"].create_index([("sender_id", 1), ("receiver_id", 1), ("is_read", 1)], background=True)
        await db["messages"].create_index([("sender_id", 1), ("receiver_id", 1), ("is_pinned", 1)], background=True)
        await db["messages"].create_index([("content", "text")], background=True)
        await db["messages"].create_index([("self_destruct_at", 1)], expireAfterSeconds=0, background=True)

        logger.info("Hoàn tất tạo chỉ mục MongoDB")
    except Exception as e:
        logger.exception("Lỗi khởi tạo chỉ mục cho MongoDB")

async def close_db():
    if database.mongodb:
        database.mongodb.close()
