from motor.motor_asyncio import AsyncIOMotorClient
import os
from loguru import logger

class DocLibDatabase:
    def __init__(self):
        self.uri = os.environ.get("MONGODB_URI")
        self.client = AsyncIOMotorClient(self.uri)
        self.db = self.client.doclib

    async def insert_document(self, document_data: dict):
        try:
            from uuid6 import uuid7
            document_data["_id"] = str(uuid7())
            res = await self.db.documents.insert_one(document_data)
            logger.success(f"[DB] Inserted document ID: {res.inserted_id}")
            return str(res.inserted_id)
        except Exception as e:
            logger.error(f"[DB Error] {e}")
            return None

    async def update_document(self, document_id: str, update_data: dict):
        try:
            from bson import ObjectId
            await self.db.documents.update_one({"_id": ObjectId(document_id)}, {"$set": update_data})
            logger.success(f"[DB] Updated document ID: {document_id}")
        except Exception as e:
            logger.error(f"[DB Update Error] {e}")

db_client = DocLibDatabase()
