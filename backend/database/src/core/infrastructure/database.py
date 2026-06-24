from src.core.infrastructure.redis_client import redis_client
import asyncio
import os

import redis.asyncio as aioredis
from loguru import logger
from src.core.infrastructure.db_client import ClientProxy

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
        logger.error("Lỗi khởi tạo do thiếu kết nối cơ sở dữ liệu")
        import sys

        sys.exit(1)

    database.mongodb = ClientProxy()

    try:
        await database.mongodb.admin.command("replSetGetStatus")
    except Exception as e:
        try:
            from urllib.parse import urlparse

            parsed_uri = urlparse(mongo_uri)
            host_with_port = (
                parsed_uri.netloc.split("@")[-1]
                if "@" in parsed_uri.netloc
                else parsed_uri.netloc
            )
            logger.info(f"Bắt đầu khởi tạo cụm cơ sở dữ liệu chính: {e}")
            await database.mongodb.admin.command(
                "replSetInitiate",
                {"_id": "rs0", "members": [{"_id": 0, "host": host_with_port}]},
            )
            logger.info(f"Khởi tạo cụm cơ sở dữ liệu thành công: {e}")
            await asyncio.sleep(3)
        except Exception as e:
            logger.warning(f"Lỗi khởi tạo cụm cơ sở dữ liệu chính: {e}")

    redis_client = aioredis.from_url(redis_uri, decode_responses=True)

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

        await db["users"].create_index([("followers_count", -1)], background=True)
        await db["users"].create_index([("email", 1)], unique=True, background=True)

        logger.info("Hoàn tất tạo chỉ mục cơ sở dữ liệu")
    except Exception as e:
        logger.error(f"Lỗi tạo chỉ mục cơ sở dữ liệu: {e}")

async def close_db():
    if database.mongodb:
        database.mongodb.close()

