from src.core.infrastructure.mongo import mongo
import os

from loguru import logger

from src.core.infrastructure.configuration import settings
from motor.motor_asyncio import AsyncIOMotorClient

class Database:
    def __init__(self):
        self.uri = settings.MONGODB_URI
        self.client = AsyncIOMotorClient(self.uri)
        self.db = self.client.doclib

    async def insert_document(self, document_data: dict):
        try:
            res = await mongo.insert_one("db_client", collection="documents", document=document_data)
            logger.info("Tạo bản ghi tài liệu thành công")
            return str(res.inserted_id)
        except Exception as e:
            logger.exception("Lỗi lưu tài liệu vào MongoDB")
            return None

    async def update_document(self, document_id: str, update_data: dict):
        try:
            from bson import ObjectId

            await self.db.documents.update_one(
                {"_id": ObjectId(document_id)}, {"$set": update_data}
            )
            logger.info("Cập nhật bản ghi tài liệu thành công")
        except Exception as e:
            logger.exception("Lỗi cập nhật dữ liệu tài liệu")

database = Database()
