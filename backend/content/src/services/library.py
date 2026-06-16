from datetime import datetime, timezone
from core.database import db_client
from core.repositories.base import RepositoryFactory
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

class LibraryService:
    @staticmethod
    async def create_reading_list(data, current_user, db=None):
        db = db or db_client.mongodb.get_default_database()
        new_list = {"_id": str(uuid7()), "user_id": str(current_user.get("id")), "name": data.name, "description": data.description, "is_public": data.is_public, "documents": [], "created_at": datetime.now(timezone.utc)}
        await RepositoryFactory.get("reading_lists").insert_one(new_list)
        logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return new_list

    @staticmethod
    async def get_my_reading_lists(current_user, db=None):
        db = db or db_client.mongodb.get_default_database()
        return await RepositoryFactory.get("reading_lists").find({"user_id": str(current_user.get("id"))}).to_list(100)

    @staticmethod
    async def get_reading_list_by_id(list_id: str, current_user, db=None):
        db = db or db_client.mongodb.get_default_database()
        reading_list = await RepositoryFactory.get("reading_lists").find_one({"_id": list_id, "user_id": str(current_user.get("id"))})
        if not reading_list: raise HTTPException(status_code=404, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        if doc_ids := reading_list.get("documents", []): reading_list["documents_detailed"] = await RepositoryFactory.get("documents").find({"_id": {"$in": doc_ids}}).to_list(length=100)
        else: reading_list["documents_detailed"] = []
        return reading_list

    @staticmethod
    async def add_document_to_list(list_id: str, document_id: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        if (await RepositoryFactory.get("reading_lists").update_one({"_id": list_id, "user_id": str(current_user.get("id"))}, {"$addToSet": {"documents": document_id}, "$set": {"updated_at": datetime.now(timezone.utc)}})).matched_count == 0:
            raise HTTPException(status_code=404, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return {"status": "success", "message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}

    @staticmethod
    async def remove_document_from_list(list_id: str, document_id: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        if (await RepositoryFactory.get("reading_lists").update_one({"_id": list_id, "user_id": str(current_user.get("id"))}, {"$pull": {"documents": document_id}, "$set": {"updated_at": datetime.now(timezone.utc)}})).matched_count == 0:
            raise HTTPException(status_code=404, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return {"status": "success", "message": "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"}