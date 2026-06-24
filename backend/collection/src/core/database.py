import os

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from shared.infrastructure.configuration import settings


class Database:
    def __init__(self):
        self.uri = settings.MONGODB_URI
        self.client = AsyncIOMotorClient(self.uri)
        self.db = self.client.doclib

    async def insert_document(self, document_data: dict):
        try:
            res = await self.db.documents.insert_one(document_data)
            logger.info("Tạo bản ghi tài liệu thành công")
            return str(res.inserted_id)
        except Exception:
            logger.error("Lỗi lưu tài liệu vào cơ sở dữ liệu")
            return None

    async def update_document(self, document_id: str, update_data: dict):
        try:
            from bson import ObjectId

            await self.db.documents.update_one(
                {"_id": ObjectId(document_id)}, {"$set": update_data}
            )
            logger.info("Cập nhật bản ghi tài liệu thành công")
        except Exception:
            logger.error("Lỗi cập nhật dữ liệu tài liệu")


database = Database()
