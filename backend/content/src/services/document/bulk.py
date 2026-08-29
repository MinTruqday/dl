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
from src.clients.knowledge import knowledge_client
from src.services.document.base import can_read_full


class DocumentBulkService:
    @staticmethod
    async def bulk_delete_documents(document_ids: List[str], current_user) -> dict:
        user_id = str(current_user.id)
        normalized_ids = sorted(
            {
                document_id.strip()
                for document_id in document_ids
                if isinstance(document_id, str) and document_id.strip()
            }
        )
        if not normalized_ids or len(normalized_ids) > 100:
            raise HTTPException(status_code=422, detail="Danh sách tài liệu cần xóa không hợp lệ")
        query = {"_id": {"$in": normalized_ids}, "creator_id": user_id, "is_deleted": {"$ne": True}}
        documents = await DocumentRepository.find(query).to_list(length=100)
        for document in documents:
            await knowledge_client.delete_document(str(document["_id"]), user_id, False)
        matched_ids = [str(document["_id"]) for document in documents]
        res = await DocumentRepository.update_many(
            {"_id": {"$in": matched_ids}, "creator_id": user_id, "is_deleted": {"$ne": True}},
            {"$set": {"is_deleted": True, "deleted_at": datetime.now(timezone.utc)}},
        )
        return {"deleted_count": res.modified_count, "document_ids": matched_ids}

    @staticmethod
    async def bulk_restore_documents(document_ids: List[str], current_user) -> dict:
        user_id = str(current_user.id)
        normalized_ids = sorted(
            {
                document_id.strip()
                for document_id in document_ids
                if isinstance(document_id, str) and document_id.strip()
            }
        )
        if not normalized_ids or len(normalized_ids) > 100:
            raise HTTPException(
                status_code=422, detail="Danh sách tài liệu cần khôi phục không hợp lệ"
            )
        query = {"_id": {"$in": normalized_ids}, "creator_id": user_id, "is_deleted": True}
        documents = await DocumentRepository.find(query).to_list(length=100)
        matched_ids = [str(document["_id"]) for document in documents]
        res = await DocumentRepository.update_many(
            {"_id": {"$in": matched_ids}, "creator_id": user_id, "is_deleted": True},
            {"$set": {"is_deleted": False, "deleted_at": None}},
        )
        from src.services.document.crud import DocumentCrudService

        for document in documents:
            if document.get("file_url"):
                await DocumentCrudService.retry_document_indexing(
                    str(document["_id"]), current_user
                )
        return {"restored_count": res.modified_count, "document_ids": matched_ids}

    @staticmethod
    async def bulk_move_documents(
        document_ids: List[str], folder_id: Optional[str], current_user
    ) -> dict:
        user_id = str(current_user.id)
        query = {"_id": {"$in": document_ids}, "creator_id": user_id}
        if folder_id:
            folder = await mongo.find_one(
                "workspace_folders", {"_id": folder_id, "creator_id": user_id}
            )
            if not folder:
                raise HTTPException(status_code=404, detail="Thư mục đích không tồn tại")
            update_op = {"$set": {"folder_id": folder_id, "updated_at": datetime.now(timezone.utc)}}
        else:
            update_op = {
                "$unset": {"folder_id": ""},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            }
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
