from datetime import datetime, timezone
from core.database import db_client
from core.repositories.base_repository import RepositoryFactory
from fastapi import HTTPException, Query
from loguru import logger
from core.config import settings

class ReadingService:
    @staticmethod
    async def get_reading_history(current_user, cursor: str = None, limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        match_stage = {"user_id": str(current_user.id)}
        if cursor: match_stage["last_read_at"] = {"$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))}
        history = await RepositoryFactory.get("reading_history").aggregate([{"$match": match_stage}, {"$sort": {"last_read_at": -1}}, {"$limit": limit}, {"$lookup": {"from": "document", "localField": "document_id", "foreignField": "_id", "as": "doc"}}, {"$unwind": {"path": "$doc", "preserveNullAndEmptyArrays": True}}, {"$lookup": {"from": "users", "localField": "doc.creator_id", "foreignField": "_id", "as": "author"}}, {"$unwind": {"path": "$author", "preserveNullAndEmptyArrays": True}}]).to_list(length=limit)
        return [{"document_id": h["document_id"], "document_title": (h.get("doc") or {}).get("title", ""), "document_slug": (h.get("doc") or {}).get("slug", ""), "author_name": (h.get("author") or {}).get("full_name") or "DocLib System", "cover_url": (h.get("doc") or {}).get("cover_url"), "progress_percentage": h.get("progress_percentage", 0), "last_read_at": (h["last_read_at"].isoformat() if isinstance(h.get("last_read_at"), datetime) else "")} for h in history]

    @staticmethod
    async def update_progress(data, current_user, db=None):
        db = db or db_client.mongodb.get_default_database()
        await RepositoryFactory.get("reading_history").update_one({"user_id": str(current_user.id), "document_id": data.document_id}, {"$set": {"progress_percentage": min(100.0, max(0.0, data.progress_percentage)), "last_read_at": datetime.now(timezone.utc)}}, upsert=True)
        return {"status": "success"}

    @staticmethod
    async def search_in_document(document_id: str, query: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id}, {"content": 1, "title": 1})
        if not doc: raise HTTPException(status_code=404, detail="Underlying designated core element completely vanished blocking sequential operational reading protocol")
        content, query_lower, content_lower, results, search_from = doc.get("content", ""), query.lower(), doc.get("content", "").lower(), [], 0
        while len(results) < 20:
            if (idx := content_lower.find(query_lower, search_from)) == -1: break
            results.append({"offset": idx, "snippet": content[max(0, idx - 60):min(len(content), idx + len(query) + 60)]})
            search_from = idx + len(query)
        return {"total": len(results), "results": results, "query": query}

    @staticmethod
    async def clear_reading_history(current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        await RepositoryFactory.get("reading_history").delete_many({"user_id": str(current_user.id)})
        return {"status": "success", "message": "Targeted active structure definitively isolated enforcing rigid explicit systemic priority queue"}

    @staticmethod
    async def delete_history_item(document_id: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        await RepositoryFactory.get("reading_history").delete_one({"user_id": str(current_user.id), "document_id": document_id})
        return {"status": "success", "message": "Targeted active structure definitively isolated enforcing rigid explicit systemic priority queue"}