from bson import ObjectId
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
            logger.info("New document record successfully generated and securely inserted primary system database collection")
            return str(res.inserted_id)
        except Exception:
            logger.error("System failed safely insert new document record database due unexpected structural constraint connectivity")
            return None

    async def update_document(self, document_id: str, update_data: dict):
        try:
            await self.db.documents.update_one(
                {"_id": ObjectId(document_id)}, {"$set": update_data}
            )
            logger.info("Requested document active record successfully updated securely saved within primary system database collection")
        except Exception:
            logger.error("Database operational engine encountered unexpected structural error attempting update specified functional document record")

db_client = DocLibDatabase()