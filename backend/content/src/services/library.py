from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger

from src.repositories.document import DocumentRepository

class LibraryService:

    @staticmethod
    @log_logic_execution
    async def create_reading_list(data, current_user):
        new_list = {
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "name": data.name,
            "description": data.description,
            "is_public": data.is_public,
            "documents": [],
            "created_at": datetime.now(timezone.utc),
        }
        await mongo.insert_one("reading_lists", new_list)
        logger.info("Reading collection created")
        return new_list

    @staticmethod
    @log_logic_execution
    async def get_my_reading_lists(current_user):
        return (
            await mongo
            .find("reading_lists", {"user_id": str(current_user.id)})
            .to_list(length=None)
        )

    @staticmethod
    @log_logic_execution
    async def get_reading_list_by_id(list_id: str, current_user):
        reading_list = await mongo.find_one(
            "reading_lists",
            {"_id": list_id, "user_id": str(current_user.id)}
        )
        if not reading_list:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy danh sách đọc yêu cầu")
        doc_ids = reading_list.get("documents", [])
        if doc_ids:
            docs = (
                await DocumentRepository
                .find({"_id": {"$in": doc_ids}})
                .to_list(length=None)
            )
            reading_list["documents_detailed"] = docs
        else:
            reading_list["documents_detailed"] = []
        return reading_list

    @staticmethod
    @log_logic_execution
    async def add_document_to_list(
        list_id: str, document_id: str, current_user
    ) -> dict:
        result = await mongo.update_one(
            "reading_lists",
            {"_id": list_id, "user_id": str(current_user.id)},
            {
                "$addToSet": {"documents": document_id},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy danh sách đọc yêu cầu")
        return {"status": "success", "message": "Thêm tài liệu vào danh sách đọc cá nhân hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def remove_document_from_list(
        list_id: str, document_id: str, current_user
    ) -> dict:
        result = await mongo.update_one(
            "reading_lists",
            {"_id": list_id, "user_id": str(current_user.id)},
            {
                "$pull": {"documents": document_id},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy danh sách đọc yêu cầu")
        return {
            "status": "success",
            "message": "Xóa tài liệu khỏi danh sách đọc cá nhân hoàn tất",
        }
