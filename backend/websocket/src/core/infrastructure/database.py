from src.core.infrastructure.redis import redis
import asyncio
import os

import redis.asyncio as aioredis
from loguru import logger

from src.core.infrastructure.configuration import settings

class DatabaseInfrastructure:
    def __init__(self):
        self.mongodb = None
        self.redis = None

database = DatabaseInfrastructure()

async def init_db():
    mongo_uri = settings.MONGODB_URI
    redis_uri = settings.REDIS_URI

    if not mongo_uri or not redis_uri :
        logger.error("Lỗi khởi tạo do thiếu kết nối Database")
        import sys

        sys.exit(1)

    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        database.mongodb = AsyncIOMotorClient(mongo_uri)
    except Exception as e:
        logger.exception("Lỗi khởi tạo kết nối Database MongoDB")

    database.redis = aioredis.from_url(redis_uri, decode_responses=True)

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

        logger.info("Hoàn tất tạo chỉ mục Database")
    except Exception as e:
        logger.exception("Lỗi khởi tạo chỉ mục cho Database")

async def close_db():
    if database.mongodb:
        database.mongodb.close()
    await database.redis.close()
