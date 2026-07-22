from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
from datetime import datetime, timezone

from fastapi import HTTPException, Query
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.repositories.document import DocumentRepository
from src.repositories.reading import ReadingRepository

class ReadingService:

    @staticmethod
    @log_logic_execution
    async def get_reading_history(
        current_user,
        cursor: str = None,
        limit: int = Query(
            default=20, le=100
        ),
    ) -> list:
        match_stage = {"user_id": str(current_user.id)}
        if cursor:
            from datetime import datetime

            match_stage["last_read_at"] = {
                "$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            }
        pipeline = [
            {"$match": match_stage},
            {"$sort": {"last_read_at": -1}},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "documents",
                    "localField": "document_id",
                    "foreignField": "_id",
                    "as": "doc",
                }
            },
            {"$unwind": {"path": "$doc", "preserveNullAndEmptyArrays": True}},
        ]
        history = (
            await mongo
            .aggregate("reading_history", pipeline)
            .to_list(length=None)
        )
        result = []
        for h in history:
            doc = h.get("doc") or {}
            result.append(
                {
                    "document_id": h["document_id"],
                    "document_title": doc.get("title", ""),
                    "document_slug": doc.get("slug", ""),
                    "author_name": doc.get("publisher_name") or "DocLib System",
                    "cover_url": doc.get("cover_url"),
                    "progress_percentage": h.get("progress_percentage", 0),
                    "last_read_at": (
                        h["last_read_at"].isoformat()
                        if isinstance(h.get("last_read_at"), datetime)
                        else ""
                    ),
                }
            )
        return result

    @staticmethod
    @log_logic_execution
    async def update_progress(data, current_user):
        user_id = str(current_user.id)
        now = datetime.now(timezone.utc)
        await ReadingRepository.update_history(
            {"user_id": user_id, "document_id": data.document_id},
            {
                "$set": {
                    "progress_percentage": min(
                        100.0, max(0.0, data.progress_percentage)
                    ),
                    "last_read_at": now,
                }
            },
            upsert=True,
        )
        return {"status": "success"}

    @staticmethod
    @log_logic_execution
    async def search_in_document(
        document_id: str, query: str, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one(
            {"_id": document_id}, {"content": 1, "title": 1}
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu yêu cầu")
        from src.services.document import DocumentService
        if not await DocumentService._can_read_full(doc, current_user):
            raise HTTPException(status_code=403, detail="Bạn không có quyền tìm kiếm trong nội dung tài liệu này")
        content = doc.get("content", "")
        query_lower = query.lower()
        content_lower = content.lower()
        results = []
        search_from = 0
        while len(results) < 20:
            idx = content_lower.find(query_lower, search_from)
            if idx == -1:
                break
            start = max(0, idx - 60)
            end = min(len(content), idx + len(query) + 60)
            snippet = content[start:end]
            results.append({"offset": idx, "snippet": snippet})
            search_from = idx + len(query)
        return {"total": len(results), "results": results, "query": query}

    @staticmethod
    @log_logic_execution
    async def clear_reading_history(current_user) -> dict:
        await ReadingRepository.delete_historys(
            {"user_id": str(current_user.id)}
        )
        return {"status": "success", "message": "Đã xóa toàn bộ dữ liệu lịch sử đọc khỏi hệ thống"}

    @staticmethod
    @log_logic_execution
    async def delete_history_item(document_id: str, current_user) -> dict:
        await ReadingRepository.delete_history(
            {"user_id": str(current_user.id), "document_id": document_id}
        )
        return {"status": "success", "message": "Xóa mục lịch sử đọc hoàn tất"}
