from datetime import datetime, timezone
from typing import List
from fastapi import HTTPException, Query
from loguru import logger

from src.core.infrastructure.mongo import mongo
from src.core.logic_logger import log_logic_execution
from src.repositories.document import DocumentRepository
from src.schemas.document import DocumentStatus
from src.services.finance_client import FinanceClient
from src.services.document.base import is_admin, serialize_document

class DocumentMetadataService:
    @staticmethod
    @log_logic_execution
    async def get_document_analytics(document_id: str, current_user):
        doc = await mongo.find_one(collection="documents", query={"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu trong kho chính")
        if doc.get("creator_id") != str(current_user.id) and not is_admin(current_user):
            raise HTTPException(
                status_code=403, detail="Bạn không có quyền xem dữ liệu phân tích tài liệu này"
            )
        views = doc.get("views", 0)
        content = doc.get("content", "")
        total_words = len(content.split()) if content else 0
        avg_read_time_min = max(1, total_words // 200)
        bookmark_count = await mongo.count_documents(
            collection="bookmarks", filter={"document_id": document_id}
        )
        purchase_count = await FinanceClient.purchase_count(document_id)
        return {
            "views": views,
            "avg_read_time": f"{avg_read_time_min} minutes",
            "avg_read_time_min": avg_read_time_min,
            "total_words": total_words,
            "saves": bookmark_count,
            "purchases": purchase_count,
        }

    @staticmethod
    @log_logic_execution
    async def get_document_academic(document_id: str, current_user):
        doc = await mongo.find_one(collection="documents", query={"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu trong kho chính")
        if (
            doc.get("creator_id") != str(current_user.id)
            and not is_admin(current_user)
            and doc.get("status") != DocumentStatus.PUBLISHED
        ):
            raise HTTPException(
                status_code=403, detail="Bạn không có quyền xem chỉ số tài liệu này"
            )
        content = doc.get("content", "")
        word_count = len(content.split()) if content else 0
        sentences = content.count(".") + content.count("!") + content.count("?") if content else 0
        avg_sentence_len = round(word_count / max(sentences, 1), 1)
        readability_score = max(0, min(100, 100 - (avg_sentence_len - 15) * 3))
        return {
            "word_count": word_count,
            "sentence_count": sentences,
            "avg_sentence_length": avg_sentence_len,
            "readability_score": round(readability_score, 1),
            "content_format": doc.get("content_format", "html"),
        }

    @staticmethod
    @log_logic_execution
    async def get_document_audit_logs(document_id: str, current_user) -> list:
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(
                status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn"
            )
        user_id = str(current_user.id)
        if doc.get("creator_id") != user_id and not is_admin(current_user):
            raise HTTPException(status_code=403, detail="Bạn không có quyền xem nhật ký kiểm toán")
        logs = await mongo.query("document_audit_logs").filter({"document_id": document_id}).sort("created_at", -1).limit(100)
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs

    @staticmethod
    @log_logic_execution
    async def get_approval_queue(cursor: str = None, limit: int = 50) -> list:
        query = {"status": DocumentStatus.PENDING_REVIEW, "is_deleted": {"$ne": True}}
        if cursor:
            query["_id"] = {"$lt": cursor}
        docs = await DocumentRepository.find(query).sort("created_at", -1).limit(limit).to_list(length=limit)
        return [serialize_document(d) for d in docs]

    @staticmethod
    @log_logic_execution
    async def get_trending_documents(limit: int = Query(default=20, le=100)) -> List[dict]:
        docs_col = DocumentRepository
        cursor = (
            docs_col.find(
                {"status": "published", "is_deleted": {"$ne": True}, "visibility": "public"}
            )
            .sort("views", -1)
            .limit(limit)
        )
        documents = await cursor.to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    @log_logic_execution
    async def get_suggested_documents(limit: int = Query(default=20, le=100)) -> List[dict]:
        docs_col = DocumentRepository
        cursor = (
            docs_col.find(
                {"status": "published", "is_deleted": {"$ne": True}, "visibility": "public"}
            )
            .sort("views", -1)
            .limit(limit)
        )
        documents = await cursor.to_list(length=limit)
        return [
            {
                "_id": str(b["_id"]),
                "slug": b.get("slug"),
                "title": b.get("title"),
                "author": b.get("author", "Unknown"),
                "cover_url": b.get("cover_url"),
                "mentions": b.get("views", 0),
            }
            for b in documents
        ]
