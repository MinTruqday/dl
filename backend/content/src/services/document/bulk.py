import io
import json
import re
import zipfile
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException
from loguru import logger

from src.repositories.document import DocumentRepository
from src.core.infrastructure.mongo import mongo
from src.services.document.base import can_read_full

class DocumentBulkService:
    @staticmethod
    async def bulk_delete_documents(document_ids: List[str], current_user) -> dict:
        user_id = str(current_user.id)
        query = {"_id": {"$in": document_ids}, "creator_id": user_id, "is_deleted": {"$ne": True}}
        res = await DocumentRepository.update_many(
            query,
            {"$set": {"is_deleted": True, "deleted_at": datetime.now(timezone.utc)}},
        )
        return {"deleted_count": res.modified_count, "document_ids": document_ids}

    @staticmethod
    async def bulk_restore_documents(document_ids: List[str], current_user) -> dict:
        user_id = str(current_user.id)
        query = {"_id": {"$in": document_ids}, "creator_id": user_id, "is_deleted": True}
        res = await DocumentRepository.update_many(
            query,
            {"$set": {"is_deleted": False, "deleted_at": None}},
        )
        return {"restored_count": res.modified_count, "document_ids": document_ids}

    @staticmethod
    async def bulk_move_documents(document_ids: List[str], folder_id: Optional[str], current_user) -> dict:
        user_id = str(current_user.id)
        query = {"_id": {"$in": document_ids}, "creator_id": user_id}
        if folder_id:
            folder = await mongo.find_one(
                "workspace_folders",
                {"_id": folder_id, "creator_id": user_id},
            )
            if not folder:
                raise HTTPException(status_code=404, detail="Thư mục đích không tồn tại")
            update_op = {"$set": {"folder_id": folder_id, "updated_at": datetime.now(timezone.utc)}}
        else:
            update_op = {"$unset": {"folder_id": ""}, "$set": {"updated_at": datetime.now(timezone.utc)}}
        res = await DocumentRepository.update_many(query, update_op)
        return {"moved_count": res.modified_count, "folder_id": folder_id}

    @staticmethod
    async def bulk_export_documents(document_ids: List[str], current_user) -> bytes:
        user_id = str(current_user.id)
        query = {"_id": {"$in": document_ids}, "is_deleted": {"$ne": True}}
        docs = await DocumentRepository.find(query).to_list(length=100)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for doc in docs:
                if not await can_read_full(doc, current_user):
                    continue
                title = re.sub(r"[^a-zA-Z0-9._ -]", "_", str(doc.get("title") or "document"))
                title = title.strip(" .")[:150] or str(doc.get("_id", "document"))
                content = doc.get("content", "")
                if not isinstance(content, str):
                    content = json.dumps(content, ensure_ascii=False)
                zf.writestr(f"{title}.txt", content)
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
