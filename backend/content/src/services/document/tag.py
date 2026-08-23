from typing import List
from fastapi import HTTPException, Query
from src.repositories.document import DocumentRepository


class DocumentTagService:
    @staticmethod
    async def get_tags_categories():
        pipeline = [
            {"$match": {"status": "published", "is_deleted": {"$ne": True}}},
            {
                "$group": {
                    "_id": None,
                    "categories": {"$addToSet": "$category"},
                    "tags": {"$push": "$tags"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "categories": 1,
                    "tags": {
                        "$reduce": {
                            "input": "$tags",
                            "initialValue": [],
                            "in": {"$setUnion": ["$$value", {"$ifNull": ["$$this", []]}]},
                        }
                    },
                }
            },
        ]
        result = await DocumentRepository.aggregate(pipeline).to_list(length=1)
        if not result:
            return {"categories": [], "tags": []}
        data = result[0]
        categories = [c for c in data.get("categories", []) if c]
        tags = [t for t in data.get("tags", []) if t]
        return {"categories": sorted(categories), "tags": sorted(tags)}

    @staticmethod
    async def get_trending_tags(limit: int = Query(default=20, le=100)) -> List[str]:
        pipeline = [
            {"$match": {"status": "published", "is_deleted": {"$ne": True}}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]
        results = await DocumentRepository.aggregate(pipeline).to_list(length=None)
        return [r["_id"] for r in results]
