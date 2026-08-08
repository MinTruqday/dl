import asyncio
from datetime import datetime, timezone

from fastapi import HTTPException
from uuid6 import uuid7

from src.core.infrastructure.mongo import mongo
from src.core.logic_logger import log_logic_execution
from src.repositories.reading import DocumentRepository


class LibraryService:
    @staticmethod
    @log_logic_execution
    async def create_reading_list(data, current_user):
        now = datetime.now(timezone.utc)
        reading_list = {
            "_id": str(uuid7()),
            "user_id": str(current_user.id),
            "name": data.name,
            "description": data.description,
            "is_public": data.is_public,
            "documents": [],
            "created_at": now,
            "updated_at": now,
        }
        await mongo.insert_one("reading_lists", reading_list)
        return reading_list

    @staticmethod
    @log_logic_execution
    async def get_my_reading_lists(current_user):
        return await mongo.find(
            "reading_lists",
            {"user_id": str(current_user.id)},
        ).sort("updated_at", -1).to_list(length=None)

    @staticmethod
    @log_logic_execution
    async def get_reading_list_by_id(list_id: str, current_user):
        reading_list = await mongo.find_one(
            "reading_lists",
            {"_id": list_id, "user_id": str(current_user.id)},
        )
        if not reading_list:
            raise HTTPException(
                status_code=404,
                detail="Hệ thống không tìm thấy danh sách đọc yêu cầu",
            )
        document_ids = reading_list.get("documents", [])
        if document_ids:
            documents = await asyncio.gather(
                *[
                    DocumentRepository.get_accessible(
                        document_id,
                        str(current_user.id),
                        current_user.is_admin(),
                    )
                    for document_id in document_ids
                ]
            )
            reading_list["documents_detailed"] = [
                document for document in documents if document
            ]
        else:
            reading_list["documents_detailed"] = []
        return reading_list

    @staticmethod
    @log_logic_execution
    async def add_document_to_list(
        list_id: str,
        document_id: str,
        current_user,
    ) -> dict:
        document = await DocumentRepository.get_accessible(
            document_id,
            str(current_user.id),
            current_user.is_admin(),
        )
        if not document:
            raise HTTPException(
                status_code=404,
                detail="Hệ thống không tìm thấy tài liệu yêu cầu",
            )
        result = await mongo.update_one(
            "reading_lists",
            {"_id": list_id, "user_id": str(current_user.id)},
            {
                "$addToSet": {"documents": document_id},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Hệ thống không tìm thấy danh sách đọc yêu cầu",
            )
        return {
            "status": "success",
            "message": "Thêm tài liệu vào danh sách đọc cá nhân hoàn tất",
        }

    @staticmethod
    @log_logic_execution
    async def remove_document_from_list(
        list_id: str,
        document_id: str,
        current_user,
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
            raise HTTPException(
                status_code=404,
                detail="Hệ thống không tìm thấy danh sách đọc yêu cầu",
            )
        return {
            "status": "success",
            "message": "Xóa tài liệu khỏi danh sách đọc cá nhân hoàn tất",
        }
