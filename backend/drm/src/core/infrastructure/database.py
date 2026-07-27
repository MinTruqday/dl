from loguru import logger

from src.core.infrastructure.configuration import settings

class DatabaseInfrastructure:
    def __init__(self):
        self.mongodb = None

database = DatabaseInfrastructure()

async def init_db():
    mongo_uri = settings.MONGODB_URI

    if not mongo_uri :
        logger.error("Failed to initialize database connection due to missing MongoDB URI")
        import sys

        sys.exit(1)

    from motor.motor_asyncio import AsyncIOMotorClient
    database.mongodb = AsyncIOMotorClient(mongo_uri)

    await setup_indexes()

async def setup_indexes():
    try:
        db = database.mongodb[settings.DRM_DB_NAME]
        await db["drm_licenses"].create_index("file_id", unique=True)
        await db["drm_licenses"].create_index([("user_id", 1), ("document_id", 1)])
        await db["drm_licenses"].create_index([("status", 1), ("created_at", -1)])
        await db["document_drm_settings"].create_index("document_id", unique=True)
        await db["copyright_disputes"].create_index([("status", 1), ("created_at", -1)])
        await db["audit_logs"].create_index([("user_id", 1), ("created_at", -1)])
        logger.info("MongoDB index creation completed")
    except Exception:
        logger.exception("Failed to create MongoDB indexes")
        raise

async def close_db():
    if database.mongodb:
        database.mongodb.close()
