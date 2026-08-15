from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, IndexModel

from src.core.infrastructure.configuration import settings


class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URI)
        self.mongodb = self.client[settings.AGENTIC_AI_DB_NAME]

    async def setup_indexes(self) -> None:
        index_sets = {
            "finetune_datasets": [
                IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)])
            ],
            "finetune_samples": [
                IndexModel([("dataset_id", ASCENDING), ("created_at", ASCENDING)])
            ],
            "finetune_jobs": [
                IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("user_id", ASCENDING), ("status", ASCENDING)]),
            ],
        }
        for collection, indexes in index_sets.items():
            await self.mongodb[collection].create_indexes(indexes)
        logger.info("Training database indexes ready")

    async def close(self) -> None:
        self.client.close()


database = Database()
