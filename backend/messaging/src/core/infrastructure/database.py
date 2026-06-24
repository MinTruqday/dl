from src.core.infrastructure.redis_client import redis_client
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

    max_retries = 5
    for i in range(max_retries):
        try:
            logger.info("Kết nối hàng đợi tin nhắn nền ổn định")
            break
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
    except Exception as e:
        logger.error(f"Lỗi tạo chỉ mục cơ sở dữ liệu: {e}")


async def close_db():
    if database.mongodb:
        database.mongodb.close()
