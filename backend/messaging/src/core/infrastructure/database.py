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
        logger.error("Lỗi khởi tạo do thiếu kết nối cơ sở dữ liệu")
        import sys

        sys.exit(1)

    from motor.motor_asyncio import AsyncIOMotorClient
    database.mongodb = AsyncIOMotorClient(mongo_uri)

    from src.core.infrastructure.mq import mq
    max_retries = 5
    for i in range(max_retries):
        try:
            if await mq.health_check():
                logger.info("Kết nối hàng đợi tin nhắn nền ổn định")
                break
            else:
                raise Exception("MQ health check failed")
        except Exception as e:
            if i == max_retries - 1:
                logger.error(f"Lỗi kết nối hàng đợi tin nhắn: {e}")
                raise e
            logger.warning(f"Đang thử kết nối lại hàng đợi: {e}")
            await asyncio.sleep(5)

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

        logger.info("Hoàn tất tạo chỉ mục cơ sở dữ liệu")
    except Exception as e:
        logger.error(f"Lỗi tạo chỉ mục cơ sở dữ liệu: {e}")

async def close_db():
    if database.mongodb:
        database.mongodb.close()
