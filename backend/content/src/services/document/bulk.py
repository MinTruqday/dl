import io
import json
import zipfile
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException
from loguru import logger

from src.core.logic_logger import log_logic_execution
from src.repositories.document import DocumentRepository
from src.services.document.base import is_admin, serialize_document

class DocumentBulkService:
    @staticmethod
    @log_logic_execution
    async def bulk_delete_documents(document_ids: List[str], current_user) -> dict:
        user_id = str(current_user.id)
        query = {"_id": {"$in": document_ids}, "creator_id": user_id, "is_deleted": {"$ne": True}}
        res = await DocumentRepository.update_many(
            query,
            {"$set": {"is_deleted": True, "deleted_at": datetime.now(timezone.utc)}},
        )
        return {"deleted_count": res.modified_count, "document_ids": document_ids}

    @staticmethod
    @log_logic_execution
    async def bulk_restore_documents(document_ids: List[str], current_user) -> dict:
        user_id = str(current_user.id)
        query = {"_id": {"$in": document_ids}, "creator_id": user_id, "is_deleted": True}
        res = await DocumentRepository.update_many(
            query,
            {"$set": {"is_deleted": False, "deleted_at": None}},
        )
        return {"restored_count": res.modified_count, "document_ids": document_ids}

    @staticmethod
    @log_logic_execution
    async def bulk_move_documents(document_ids: List[str], folder_id: Optional[str], current_user) -> dict:
        user_id = str(current_user.id)
        query = {"_id": {"$in": document_ids}, "creator_id": user_id}
        if folder_id:
            update_op = {"$set": {"folder_id": folder_id, "updated_at": datetime.now(timezone.utc)}}
        else:
            update_op = {"$unset": {"folder_id": ""}, "$set": {"updated_at": datetime.now(timezone.utc)}}
        res = await DocumentRepository.update_many(query, update_op)
        return {"moved_count": res.modified_count, "folder_id": folder_id}

    @staticmethod
    @log_logic_execution
    async def bulk_export_documents(document_ids: List[str], current_user) -> bytes:
        user_id = str(current_user.id)
        query = {"_id": {"$in": document_ids}, "$or": [{"creator_id": user_id}, {"visibility": "public"}]}
        docs = await DocumentRepository.find(query).to_list(length=100)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for doc in docs:
                title = doc.get("title", "document").replace("/", "_")
                content = doc.get("content", "")
                zf.writestr(f"{title}.txt", content)
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
