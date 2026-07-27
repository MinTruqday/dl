from loguru import logger

from src.core.infrastructure.configuration import settings


class DatabaseInfrastructure:
    def __init__(self):
        self.mongodb = None


database = DatabaseInfrastructure()


async def init_db():
    from motor.motor_asyncio import AsyncIOMotorClient

    database.mongodb = AsyncIOMotorClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=5000,
    )
    await database.mongodb.admin.command("ping")
    await setup_indexes()


async def setup_indexes():
    db = database.mongodb[settings.NOTIFICATION_DB_NAME]
    await db["notifications"].create_index(
        [("target_user_id", 1), ("created_at", -1)]
    )
    await db["notifications"].create_index(
        [("target_user_id", 1), ("is_read", 1)]
    )
    await db["notifications"].create_index(
        "idempotency_key",
        unique=True,
        partialFilterExpression={"idempotency_key": {"$type": "string"}},
    )
    logger.info("Notification database indexes initialized")


async def close_db():
    if database.mongodb:
        database.mongodb.close()
        database.mongodb = None
