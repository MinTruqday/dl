import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

from shared.infrastructure.database import database
from shared.repositories.base_repository import RepositoryFactory


class LibraryService:

    @staticmethod
    async def create_reading_list(data, current_user, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        new_list = {
            "_id": str(uuid7()),
            "user_id": str(current_user.id),
            "name": data.name,
            "description": data.description,
            "is_public": data.is_public,
            "documents": [],
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("reading_lists").insert_one(new_list)
        logger.info("Tạo bộ sưu tập đọc cá nhân thành công")
        return new_list

    @staticmethod
    async def get_my_reading_lists(current_user, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        return (
            await RepositoryFactory.get("reading_lists")
            .find({"user_id": str(current_user.id)})
            .to_list(100)
        )

    @staticmethod
    async def get_reading_list_by_id(list_id: str, current_user, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        reading_list = await RepositoryFactory.get("reading_lists").find_one(
            {"_id": list_id, "user_id": str(current_user.id)}
        )
        if not reading_list:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh sách đọc")
        doc_ids = reading_list.get("documents", [])
        if doc_ids:
            docs = (
                await RepositoryFactory.get("documents")
                .find({"_id": {"$in": doc_ids}})
                .to_list(length=100)
            )
            reading_list["documents_detailed"] = docs
        else:
            reading_list["documents_detailed"] = []
        return reading_list

    @staticmethod
    async def add_document_to_list(
        list_id: str, document_id: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        result = await RepositoryFactory.get("reading_lists").update_one(
            {"_id": list_id, "user_id": str(current_user.id)},
            {
                "$addToSet": {"documents": document_id},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh sách đọc")
        return {"status": "success", "message": "Đã thêm tài liệu vào danh sách đọc"}

    @staticmethod
    async def remove_document_from_list(
        list_id: str, document_id: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        result = await RepositoryFactory.get("reading_lists").update_one(
            {"_id": list_id, "user_id": str(current_user.id)},
            {
                "$pull": {"documents": document_id},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh sách đọc")
        return {
            "status": "success",
            "message": "Xóa tài liệu khỏi bộ sưu tập đọc thành công",
        }
