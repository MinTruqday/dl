from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from loguru import logger

from src.clients.authentication import AuthenticationClient
from src.repositories.document import DocumentRepository
from src.repositories.folder import FolderRepository


class DocumentHierarchyService:
    @staticmethod
    async def get_folders(parent_id: Optional[str], current_user) -> list:
        query = {"creator_id": str(current_user.id)}
        if parent_id:
            query["parent_id"] = parent_id
        cursor = FolderRepository.query().filter(query).sort("created_at", 1)
        folders = await cursor
        for f in folders:
            f["_id"] = str(f["_id"])
        return folders

    @staticmethod
    async def create_folder(name: str, parent_id: Optional[str], current_user) -> dict:
        folder_doc = {
            "name": name,
            "parent_id": parent_id,
            "creator_id": str(current_user.id),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        res = await FolderRepository.insert_one(folder_doc)
        folder_doc["_id"] = str(res.inserted_id)
        return folder_doc

    @staticmethod
    async def delete_folder(folder_id: str, current_user) -> dict:
        folder = await FolderRepository.find_one(
            {"_id": folder_id, "creator_id": str(current_user.id)}
        )
        if not folder:
            raise HTTPException(status_code=404, detail="Không tìm thấy thư mục làm việc")
        await FolderRepository.delete_one({"_id": folder_id})
        await DocumentRepository.update_many(
            {"folder_id": folder_id}, {"$unset": {"folder_id": ""}}
        )
        return {"deleted": True}

    @staticmethod
    async def move_document_to_folder(
        document_id: str, folder_id: Optional[str], current_user
    ) -> dict:
        user_id = str(current_user.id)
        doc = await DocumentRepository.find_one({"_id": document_id, "creator_id": user_id})
        if not doc:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài liệu hoặc bạn không có quyền di chuyển"
            )
        if folder_id:
            folder = await FolderRepository.find_one(
                {"_id": folder_id, "creator_id": user_id}
            )
            if not folder:
                raise HTTPException(status_code=404, detail="Thư mục đích không tồn tại")
            await DocumentRepository.update_one(
                {"_id": document_id},
                {"$set": {"folder_id": folder_id, "updated_at": datetime.now(timezone.utc)}},
            )
        else:
            await DocumentRepository.update_one(
                {"_id": document_id},
                {"$unset": {"folder_id": ""}, "$set": {"updated_at": datetime.now(timezone.utc)}},
            )
        return {"status": "moved", "document_id": document_id, "folder_id": folder_id}

    @staticmethod
    async def transfer_document(document_id: str, new_owner_id: str, current_user) -> dict:
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài liệu hoặc không có quyền truy cập"
            )
        try:
            target = await AuthenticationClient.get_account(new_owner_id)
        except Exception:
            logger.exception("Failed to verify ownership transfer target")
            raise HTTPException(
                status_code=503, detail="Dịch vụ hồ sơ người dùng tạm thời không khả dụng"
            )
        if not target:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản chuyển nhượng")
        await DocumentRepository.update_one(
            {"_id": document_id},
            {"$set": {"creator_id": new_owner_id, "updated_at": datetime.now(timezone.utc)}},
        )
        return {"status": "transferred", "new_owner_id": new_owner_id}
