from motor.motor_asyncio import AsyncIOMotorClient
import os
from core.config import settings
from loguru import logger

class DocLibDatabase:
    def __init__(self):
        self.uri = settings.MONGODB_URI
        self.client = AsyncIOMotorClient(self.uri)
        self.db = self.client.doclib

    async def insert_document(self, document_data: dict):
        try:
            res = await self.db.documents.insert_one(document_data)
            logger.success(f"Đã thêm mới tài liệu mang mã: {res.inserted_id}")
            return str(res.inserted_id)
        except Exception as e:
            logger.error(f"Lỗi: {e}")
            return None

    async def update_document(self, document_id: str, update_data: dict):
        try:
            from bson import ObjectId
            await self.db.documents.update_one({"_id": ObjectId(document_id)}, {"$set": update_data})
            logger.success(f"Đã cập nhật tài liệu mang mã: {document_id}")
        except Exception as e:
            logger.error(f"Lỗi: {e}")

db_client = DocLibDatabase()
