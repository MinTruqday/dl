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
            logger.success(f"Successfully inserted new document with ID: {res.inserted_id}")
            return str(res.inserted_id)
        except Exception as e:
            logger.error("Failed to insert document")
            return None

    async def update_document(self, document_id: str, update_data: dict):
        try:
            from bson import ObjectId

            await self.db.documents.update_one(
                {"_id": ObjectId(document_id)}, {"$set": update_data}
            )
            logger.success(f"Successfully updated document: {document_id}")
        except Exception as e:
            logger.error("Failed to update document")


db_client = DocLibDatabase()
