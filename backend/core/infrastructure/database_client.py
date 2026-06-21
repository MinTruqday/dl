import asyncio
import os

import aio_pika
import redis.asyncio as aioredis
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from core.config import settings


class DBClient:
    def __init__(self):
        self.mongodb = None
        self.redis = None
        self.rabbitmq = None


db_client = DBClient()


async def init_db():
    mongo_uri = settings.MONGODB_URI
    redis_uri = settings.REDIS_URI
    rabbitmq_uri = settings.RABBITMQ_URI

    if not mongo_uri or not redis_uri or not rabbitmq_uri:
        logger.error("Lỗi khởi tạo do thiếu kết nối cơ sở dữ liệu")
        import sys

        sys.exit(1)

    db_client.mongodb = AsyncIOMotorClient(mongo_uri, maxPoolSize=1000)

    try:
        await db_client.mongodb.admin.command("replSetGetStatus")
    except Exception:
        try:
            from urllib.parse import urlparse

            parsed_uri = urlparse(mongo_uri)
            host_with_port = (
                parsed_uri.netloc.split("@")[-1]
                if "@" in parsed_uri.netloc
                else parsed_uri.netloc
            )
            logger.info("Bắt đầu khởi tạo cụm cơ sở dữ liệu chính")
            await db_client.mongodb.admin.command(
                "replSetInitiate",
                {"_id": "rs0", "members": [{"_id": 0, "host": host_with_port}]},
            )
            logger.info("Khởi tạo cụm cơ sở dữ liệu thành công")
            await asyncio.sleep(3)
        except Exception:
            logger.warning("Lỗi khởi tạo cụm cơ sở dữ liệu chính")

    db_client.redis = aioredis.from_url(redis_uri, decode_responses=True)

    max_retries = 5
    for i in range(max_retries):
        try:
            db_client.rabbitmq = await aio_pika.connect_robust(rabbitmq_uri)
            logger.info("Kết nối hàng đợi tin nhắn nền ổn định")
            break
        except Exception as e:
            if i == max_retries - 1:
                logger.error("Lỗi kết nối hàng đợi tin nhắn")
                raise e
            logger.warning("Đang thử kết nối lại hàng đợi")
            await asyncio.sleep(5)

    await setup_indexes()


async def setup_indexes():
    try:
        db = db_client.mongodb[settings.SERVICE_DB_NAME]

        await db["documents"].create_index(
            [("title", "text"), ("description", "text"), ("author", "text")],
            background=True,
        )
        await db["documents"].create_index([("creator_id", 1)], background=True)
        await db["documents"].create_index(
            [("status", 1), ("is_deleted", 1), ("created_at", -1)], background=True
        )
        await db["documents"].create_index(
            [("status", 1), ("is_deleted", 1), ("views", -1)], background=True
        )
        await db["documents"].create_index(
        )
        await db["documents"].create_index(
            [("status", 1), ("is_deleted", 1), ("categories", 1), ("created_at", -1)],
            background=True,
        )
        await db["documents"].create_index(
            [("status", 1), ("is_deleted", 1), ("tags", 1), ("created_at", -1)],
            background=True,
        )
        await db["documents"].create_index([("slug", 1)], unique=True, background=True)

        await db["status_updates"].create_index([("created_at", -1)], background=True)
        await db["status_updates"].create_index([("user_id", 1)], background=True)
        await db["status_updates"].create_index(
            [("is_shadowbanned", 1)], background=True
        )

        await db["comments"].create_index(
            [("item_id", 1), ("item_type", 1)], background=True
        )
        await db["comments"].create_index([("path", 1)], background=True)

        await db["users"].create_index([("followers_count", -1)], background=True)
        await db["users"].create_index([("email", 1)], unique=True, background=True)

        await db["transactions"].create_index([("user_id", 1)], background=True)
        await db["reports"].create_index([("status", 1)], background=True)
        await db["reports"].create_index([("created_at", -1)], background=True)

        await db["editor_comments"].create_index(
            [("document_id", 1), ("block_id", 1)], background=True
        )
        await db["document_versions"].create_index(
            [("document_id", 1), ("created_at", -1)], background=True
        )

        await db["conversations"].create_index(
            [("participants", 1), ("updated_at", -1)], background=True
        )

        await db["messages"].create_index(
            [("sender_id", 1), ("receiver_id", 1), ("created_at", -1)], background=True
        )
        await db["messages"].create_index(
            [("sender_id", 1), ("receiver_id", 1), ("is_read", 1)], background=True
        )
        await db["messages"].create_index(
            [("sender_id", 1), ("receiver_id", 1), ("is_pinned", 1)], background=True
        )
        await db["messages"].create_index([("content", "text")], background=True)
        await db["messages"].create_index(
            [("self_destruct_at", 1)], expireAfterSeconds=0, background=True
        )

        await db["storage_items"].create_index(
            [("owner_id", 1), ("parent_id", 1), ("is_trashed", 1)], background=True
        )
        await db["storage_items"].create_index(
            [("shared_with.user_id", 1), ("parent_id", 1), ("is_trashed", 1)],
            background=True,
        )
        await db["storage_items"].create_index([("url", 1)], background=True)
        await db["storage_items"].create_index([("target_id", 1)], background=True)
        await db["storage_items"].create_index(
            [("owner_id", 1), ("is_trashed", 1), ("updated_at", -1)], background=True
        )

        logger.info("Hoàn tất tạo chỉ mục cơ sở dữ liệu")
    except Exception:
        logger.error("Lỗi tạo chỉ mục cơ sở dữ liệu")


async def close_db():
    if db_client.mongodb:
        db_client.mongodb.close()
    if db_client.redis:
        await db_client.redis.close()
    if db_client.rabbitmq:
        await db_client.rabbitmq.close()
