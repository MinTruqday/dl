from datetime import datetime, timezone

from loguru import logger
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database as infrastructure


class Database:
    def get_collection(self):
        if infrastructure.mongodb is None:
            raise RuntimeError("MongoDB connection is not initialized")
        return infrastructure.mongodb[settings.CONTENT_DB_NAME]["documents"]

    async def insert_document(self, document_data: dict):
        now = datetime.now(timezone.utc)
        document = {
            "_id": str(uuid7()),
            "created_at": now,
            "updated_at": now,
            **document_data,
        }
        identity = document.get("source_url") or document.get("file_url")
        if not identity:
            raise ValueError("Collected document requires a source identity")
        query = (
            {"source_url": identity}
            if document.get("source_url")
            else {"file_url": identity}
        )
        result = await self.get_collection().find_one_and_update(
            query,
            {"$setOnInsert": document},
            upsert=True,
            return_document=True,
        )
        logger.info("Collected document record persisted successfully")
        return str(result["_id"])

    async def update_document(self, document_id: str, update_data: dict):
        result = await self.get_collection().update_one(
            {"_id": document_id},
            {"$set": {**update_data, "updated_at": datetime.now(timezone.utc)}},
        )
        return result.modified_count == 1


database = Database()
