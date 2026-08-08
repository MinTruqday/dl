from typing import Any, List, Optional
import httpx
from loguru import logger
from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.configuration import settings
from src.repositories.reading import DocumentRepository, ReadingRepository

class DiscoveryService:

    @staticmethod
    @log_logic_execution
    async def get_tags_categories() -> dict:
        pipeline = [
            {"$match": {"status": "published", "is_public": True}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 50},
        ]
        tags_data = await DocumentRepository.find({"status": "published", "is_public": True}).to_list(length=None)
        tags_count = {}
        for d in tags_data:
            for t in d.get("tags", []):
                tags_count[t] = tags_count.get(t, 0) + 1
        sorted_tags = sorted([{"tag": k, "count": v} for k, v in tags_count.items()], key=lambda x: x["count"], reverse=True)[:50]
        return {"tags": sorted_tags}

    @staticmethod
    @log_logic_execution
    async def get_trending_documents(limit: int = 20) -> list:
        docs = (
            await DocumentRepository
            .find({"status": "published", "is_public": True})
            .sort("views", -1)
            .limit(limit)
            .to_list(length=limit)
        )
        return [
            {
                "_id": str(d["_id"]),
                "title": d.get("title", ""),
                "slug": d.get("slug", ""),
                "cover_url": d.get("cover_url"),
                "author_name": d.get("publisher_name") or "DocLib Author",
                "views": d.get("views", 0),
                "summary": d.get("summary", ""),
            }
            for d in docs
        ]

    @staticmethod
    @log_logic_execution
    async def get_personalized_recommendations(user_id: str, limit: int = 20) -> list:
        history = await ReadingRepository.find({"user_id": user_id}).sort("last_read_at", -1).limit(10).to_list(length=10)
        read_doc_ids = [h.get("document_id") for h in history if h.get("document_id")]
        
        if not read_doc_ids:
            return await DiscoveryService.get_trending_documents(limit)

        read_docs = await DocumentRepository.find({"_id": {"$in": read_doc_ids}}).to_list(length=10)
        tags_set = set()
        for d in read_docs:
            for t in d.get("tags", []):
                tags_set.add(t)

        if not tags_set:
            return await DiscoveryService.get_trending_documents(limit)

        recommended = (
            await DocumentRepository
            .find({"status": "published", "is_public": True, "tags": {"$in": list(tags_set)}, "_id": {"$nin": read_doc_ids}})
            .sort("views", -1)
            .limit(limit)
            .to_list(length=limit)
        )
        
        if len(recommended) < limit:
            fallback = await DiscoveryService.get_trending_documents(limit)
            seen = {str(r["_id"]) for r in recommended}
            for f in fallback:
                if str(f["_id"]) not in seen and str(f["_id"]) not in read_doc_ids:
                    recommended.append(f)
                    seen.add(str(f["_id"]))
                    if len(recommended) >= limit:
                        break

        return [
            {
                "_id": str(d["_id"]),
                "title": d.get("title", ""),
                "slug": d.get("slug", ""),
                "cover_url": d.get("cover_url"),
                "author_name": d.get("publisher_name") or "DocLib Author",
                "views": d.get("views", 0),
                "summary": d.get("summary", ""),
            }
            for d in recommended
        ]
