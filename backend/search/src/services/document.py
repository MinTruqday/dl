from typing import List, Optional
from fastapi import Query
from src.repositories.document import DocumentRepository

def serialize_document(doc: dict | None) -> dict | None:
    if not doc:
        return None
    res = dict(doc)
    res["_id"] = str(res["_id"])
    if "created_at" in res and hasattr(res["created_at"], "isoformat"):
        res["created_at"] = res["created_at"].isoformat()
    if "updated_at" in res and hasattr(res["updated_at"], "isoformat"):
        res["updated_at"] = res["updated_at"].isoformat()
    return res

class DocumentService:

    @staticmethod
    async def search_documents(query: str, limit: int = Query(default=20, le=100)) -> List[dict]:
        cursor = DocumentRepository.find(
            {
                "status": "published",
                "is_deleted": {"$ne": True},
                "visibility": "public",
                "$text": {"$search": query},
            }
        ).limit(limit)
        documents = await cursor.to_list(length=limit)
        if not documents:
            cursor = DocumentRepository.find(
                {
                    "status": "published",
                    "is_deleted": {"$ne": True},
                    "visibility": "public",
                    "$or": [
                        {"title": {"$regex": query, "$options": "i"}},
                        {"description": {"$regex": query, "$options": "i"}},
                        {"tags": {"$regex": query, "$options": "i"}},
                    ],
                }
            ).limit(limit)
            documents = await cursor.to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    async def get_ranked_public_documents(ranked_results: List[dict], limit: int) -> List[dict]:
        document_ids = [
            str(result["document_id"])
            for result in ranked_results
            if isinstance(result, dict) and result.get("document_id")
        ][:limit]
        if not document_ids:
            return []
        documents = await DocumentRepository.find(
            {
                "_id": {"$in": document_ids},
                "status": "published",
                "is_deleted": {"$ne": True},
                "visibility": "public",
            }
        ).to_list(length=limit)
        by_id = {str(document["_id"]): document for document in documents}
        scores = {
            str(result["document_id"]): float(result.get("score") or 0)
            for result in ranked_results
            if isinstance(result, dict) and result.get("document_id")
        }
        return [
            {**serialize_document(by_id[document_id]), "semantic_score": scores.get(document_id, 0)}
            for document_id in document_ids
            if document_id in by_id
        ]
