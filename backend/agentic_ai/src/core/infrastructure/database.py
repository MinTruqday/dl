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

    from src.core.infrastructure.mq import mq
    max_retries = 5
    for i in range(max_retries):
        try:
            if await mq.health_check():
                logger.info("Kết nối RabbitMQ ổn định")
                break
            else:
                raise Exception("MQ health check failed")
        except Exception as e:
            if i == max_retries - 1:
                logger.exception("Lỗi kết nối RabbitMQ")
                raise e
            logger.exception("Đang thử kết nối lại RabbitMQ")
            await asyncio.sleep(5)

    await setup_indexes()

async def setup_indexes():
    try:
        db = database.mongodb[settings.SERVICE_DB_NAME]
        logger.info("Hoàn tất tạo chỉ mục MongoDB")
    except Exception as e:
        logger.exception("Lỗi khởi tạo chỉ mục cho MongoDB")

async def close_db():
    if database.mongodb:
        database.mongodb.close()

