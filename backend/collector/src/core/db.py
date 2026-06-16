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
            logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
            return str(res.inserted_id)
        except Exception:
            logger.error("Lỗi truy xuất cơ sở dữ liệu hệ thống")
            return None

    async def update_document(self, document_id: str, update_data: dict):
        try:
            await self.db.documents.update_one(
                {"_id": ObjectId(document_id)}, {"$set": update_data}
            )
            logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        except Exception:
            logger.error("Lỗi truy xuất cơ sở dữ liệu hệ thống")

db_client = DocLibDatabase()