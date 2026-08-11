import sys
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.infrastructure.configuration import settings

class DatabaseInfrastructure:
    def __init__(self):
        self.mongodb = None

database = DatabaseInfrastructure()

async def init_db():
    mongo_uri = settings.MONGODB_URI
    if not mongo_uri:
        logger.error("Failed to initialize database connection due to missing MongoDB URI")
        sys.exit(1)

    database.mongodb = AsyncIOMotorClient(mongo_uri)
    await setup_indexes()

async def setup_indexes():
    try:
        db = database.mongodb[settings.COLLABORATION_DB_NAME]
        await db["collaboration_invites"].create_index([("invitee_id", 1), ("status", 1)], background=True)
        await db["collaboration_invites"].create_index([("document_id", 1), ("status", 1)], background=True)
        await db["collaboration_invites"].create_index([("document_id", 1), ("invitee_id", 1)], background=True)
        await db["collaboration_activities"].create_index([("document_id", 1), ("timestamp", -1)], background=True)
        await db["collaboration_status"].create_index([("document_id", 1), ("user_id", 1)], unique=True, background=True)
        await db["collaboration_drafts"].create_index([("document_id", 1), ("timestamp", -1)], background=True)
        await db["collaboration_locks"].create_index([("document_id", 1)], unique=True, background=True)
        await db["collaboration_invite_codes"].create_index([("invite_code", 1)], unique=True, background=True)
        await db["collaboration_invite_codes"].create_index([("document_id", 1)], unique=True, background=True)
        await db["collaboration_tasks"].create_index([("document_id", 1), ("created_at", -1)], background=True)
        await db["collaboration_task_comments"].create_index([("task_id", 1), ("timestamp", 1)], background=True)
        await db["collaboration_share_links"].create_index([("document_id", 1)], unique=True, background=True)
        await db["collaboration_share_links"].create_index([("share_token", 1)], unique=True, background=True)
        await db["collaboration_access_requests"].create_index([("document_id", 1), ("user_id", 1), ("status", 1)], background=True)
        await db["collaboration_access_requests"].create_index([("creator_id", 1), ("status", 1)], background=True)
        logger.info("MongoDB index initialization completed")
    except Exception:
        logger.exception("Failed to initialize MongoDB collection indexes")
        raise

async def close_db():
    if database.mongodb:
        database.mongodb.close()
