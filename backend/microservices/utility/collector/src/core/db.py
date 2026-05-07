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
            res = await self.db.documents.insert_one(document_data)
logger.info("Log message sanitized"))
            return str(res.inserted_id)
        except Exception as e:
logger.info("Log message sanitized"))
            return None
    async def update_document(self, document_id: str, update_data: dict):
        try:
            from bson import ObjectId
            await self.db.documents.update_one({"_id": ObjectId(document_id)}, {"$set": update_data})
logger.info("Log message sanitized"))
        except Exception as e:
logger.info("Log message sanitized"))
db_client = DocLibDatabase()
