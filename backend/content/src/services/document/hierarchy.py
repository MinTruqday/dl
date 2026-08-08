from datetime import datetime, timezone
from typing import List, Optional
import httpx
from fastapi import HTTPException
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.mongo import mongo
from src.core.logic_logger import log_logic_execution
from src.repositories.document import DocumentRepository
from src.services.document.base import is_admin

class DocumentHierarchyService:
    @staticmethod
    @log_logic_execution
    async def get_folders(parent_id: Optional[str], current_user) -> list:
        query = {"creator_id": str(current_user.id)}
        if parent_id:
            query["parent_id"] = parent_id
        cursor = mongo.query("workspace_folders").filter(query).sort("created_at", 1)
        folders = await cursor
        for f in folders:
            f["_id"] = str(f["_id"])
        return folders

    @staticmethod
    @log_logic_execution
    async def create_folder(name: str, parent_id: Optional[str], current_user) -> dict:
        folder_doc = {
            "name": name,
            "parent_id": parent_id,
            "creator_id": str(current_user.id),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        res = await mongo.insert_one(collection="workspace_folders", document=folder_doc)
        folder_doc["_id"] = str(res.inserted_id)
        return folder_doc

    @staticmethod
    @log_logic_execution
    async def delete_folder(folder_id: str, current_user) -> dict:
        folder = await mongo.find_one(
            "workspace_folders", {"_id": folder_id, "creator_id": str(current_user.id)}
        )
        if not folder:
            raise HTTPException(status_code=404, detail="Không tìm thấy thư mục làm việc")
        await mongo.delete_one("workspace_folders", {"_id": folder_id})
        await mongo.update_many(
            "documents", {"folder_id": folder_id}, {"$unset": {"folder_id": ""}}
        )
        return {"deleted": True}

    @staticmethod
    @log_logic_execution
    async def move_document_to_folder(document_id: str, folder_id: Optional[str], current_user) -> dict:
        user_id = str(current_user.id)
        doc = await DocumentRepository.find_one({"_id": document_id, "creator_id": user_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu hoặc bạn không có quyền di chuyển")
        if folder_id:
            folder = await mongo.find_one("workspace_folders", {"_id": folder_id, "creator_id": user_id})
            if not folder:
                raise HTTPException(status_code=404, detail="Thư mục đích không tồn tại")
            await DocumentRepository.update_one({"_id": document_id}, {"$set": {"folder_id": folder_id, "updated_at": datetime.now(timezone.utc)}})
        else:
            await DocumentRepository.update_one({"_id": document_id}, {"$unset": {"folder_id": ""}, "$set": {"updated_at": datetime.now(timezone.utc)}})
        return {"status": "moved", "document_id": document_id, "folder_id": folder_id}

    @staticmethod
    @log_logic_execution
    async def transfer_document(document_id: str, new_owner_id: str, current_user) -> dict:
        doc = await mongo.find_one(
            "documents", {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài liệu hoặc không có quyền truy cập"
            )
        target = None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{settings.HUMANITY_URL}/nguoi-dung/{new_owner_id}",
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
                if resp.status_code == 200:
                    target = resp.json().get("data")
        except Exception:
            logger.exception("Failed to verify ownership transfer target")
            raise HTTPException(
                status_code=503, detail="Dịch vụ hồ sơ người dùng tạm thời không khả dụng"
            )
        if not target:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản chuyển nhượng")
        await mongo.update_one(
            "documents",
            {"_id": document_id},
            {"$set": {"creator_id": new_owner_id, "updated_at": datetime.now(timezone.utc)}},
        )
        return {"status": "transferred", "new_owner_id": new_owner_id}
