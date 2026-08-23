import json
from datetime import datetime, timezone
from typing import List
from fastapi import HTTPException, Query
from loguru import logger

from src.core.infrastructure.mongo import mongo
from src.repositories.document import DocumentRepository
from src.schemas.document import DocumentStatus
from src.services.document.base import can_read_full, is_admin, serialize_document

class DocumentMetadataService:
    @staticmethod
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
        text_content = (
            content
            if isinstance(content, str)
            else json.dumps(content, ensure_ascii=False)
        )
        total_words = len(text_content.split()) if text_content else 0
        avg_read_time_min = max(1, total_words // 200)
        return {
            "views": views,
            "avg_read_time": f"{avg_read_time_min} minutes",
            "avg_read_time_min": avg_read_time_min,
            "total_words": total_words,
        }

    @staticmethod
    async def get_document_academic(document_id: str, current_user):
        doc = await mongo.find_one(collection="documents", query={"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu trong kho chính")
        if not await can_read_full(doc, current_user):
            raise HTTPException(
                status_code=403, detail="Bạn không có quyền xem chỉ số tài liệu này"
            )
        content = doc.get("content", "")
        text_content = (
            content
            if isinstance(content, str)
            else json.dumps(content, ensure_ascii=False)
        )
        word_count = len(text_content.split()) if text_content else 0
        sentences = (
            text_content.count(".")
            + text_content.count("!")
            + text_content.count("?")
            if text_content
            else 0
        )
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
    async def get_approval_queue(cursor: str = None, limit: int = 50) -> list:
        query = {
            "status": DocumentStatus.PROCESSING_PUBLISH,
            "is_deleted": {"$ne": True},
        }
        if cursor:
            query["updated_at"] = {
                "$gt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            }
        documents = await DocumentRepository.find(query).sort("updated_at", 1).limit(
            limit
        ).to_list(length=limit)

        def format_date(value):
            if isinstance(value, datetime):
                return value.isoformat()
            if isinstance(value, str):
                return value
            return datetime.now(timezone.utc).isoformat()

        return [
            {
                "_id": str(document["_id"]),
                "title": document.get("title", ""),
                "description": document.get("description", ""),
                "creator_id": document.get("creator_id"),
                "author_name": document.get("publisher_name") or "Anonymous",
                "created_at": format_date(
                    document.get("created_at") or document.get("updated_at")
                ),
                "updated_at": format_date(document.get("updated_at")),
                "submitted_at": format_date(document.get("updated_at")),
            }
            for document in documents
        ]

    @staticmethod
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
