import os

from core.config import settings
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient


class DocLibDatabase:
    def __init__(self):
        self.uri = settings.MONGODB_URI
        self.client = AsyncIOMotorClient(self.uri)
        self.db = self.client.doclib

    async def insert_document(self, document_data: dict):
        try:
            res = await self.db.documents.insert_one(document_data)
            logger.info("A new document record has been successfully generated and securely inserted into the primary database")
            return str(res.inserted_id)
        except Exception:
            logger.error("The system failed to safely insert the new document record into the database due to a constraint or connectivity issue")
            return None

    async def update_document(self, document_id: str, update_data: dict):
        try:
            from bson import ObjectId

            await self.db.documents.update_one(
                {"_id": ObjectId(document_id)}, {"$set": update_data}
            )
            logger.info("The requested document record has been successfully updated and saved within the primary database")
        except Exception:
            logger.error("The database engine encountered an unexpected error while attempting to update the specified document record")


db_client = DocLibDatabase()