from typing import List, Optional, Any
from datetime import datetime
from shared.core.database import db_client
from loguru import logger

class RankService:
    @staticmethod
    async def get_contribution_ranking(limit: int = 5) -> List[dict]:
        db = db_client.mongodb.get_default_database()
        users_col = db["users"]
        pipeline = [
            {"$match": {"role": {"$in": ["AUTHOR", "ADMIN"]}, "is_active": True}},
            {"$lookup": {
                "from": "documents",
                "localField": "_id",
                "foreignField": "author_id",
                "as": "user_documents"
            }},
            {"$project": {
                "full_name": 1,
                "avatar_url": 1,
                "role": 1,
                "document_count": {"$size": "$user_documents"},
                "total_views": {"$sum": "$user_documents.views"}
            }},
            {"$sort": {"total_views": -1, "document_count": -1}},
            {"$limit": limit}
        ]
        results = await users_col.aggregate(pipeline).to_list(length=limit)
        return [{
            "id": str(r["_id"]),
            "full_name": r.get("full_name", "Ẩn danh"),
            "avatar_url": r.get("avatar_url"),
            "role": r.get("role", "READER"),
            "score": r.get("total_views", 0) + (r.get("document_count", 0) * 10)
        } for r in results]

    @staticmethod
    async def get_reader_ranking(limit: int = 5) -> List[dict]:
        db = db_client.mongodb.get_default_database()
        users_col = db["users"]
        pipeline = [
            {"$match": {"role": "READER", "is_active": True}},
            {"$lookup": {
                "from": "comments",
                "localField": "_id",
                "foreignField": "user_id",
                "as": "user_comments"
            }},
            {"$lookup": {
                "from": "status_updates",
                "localField": "_id",
                "foreignField": "user_id",
                "as": "user_posts"
            }},
            {"$project": {
                "full_name": 1,
                "avatar_url": 1,
                "role": 1,
                "comment_count": {"$size": "$user_comments"},
                "post_count": {"$size": "$user_posts"}
            }},
            {"$addFields": {
                "score": {"$add": [
                    {"$multiply": ["$comment_count", 5]},
                    {"$multiply": ["$post_count", 10]}
                ]}
            }},
            {"$sort": {"score": -1}},
            {"$limit": limit}
        ]
        results = await users_col.aggregate(pipeline).to_list(length=limit)
        return [{
            "id": str(r["_id"]),
            "full_name": r.get("full_name", "Độc giả ẩn danh"),
            "avatar_url": r.get("avatar_url"),
            "role": r.get("role", "READER"),
            "score": r.get("score", 0)
        } for r in results]

    @staticmethod
    async def get_featured_authors(limit: int = 10) -> list:
        db = db_client.mongodb.get_default_database()
        authors = await db["users"].find({"role": "AUTHOR", "is_active": True}).sort("created_at", -1).limit(limit).to_list(length=limit)
        return [{
            "id": str(a["_id"]),
            "full_name": a.get("full_name", "Tác giả ẩn danh"),
            "avatar_url": a.get("avatar_url"),
            "bio": a.get("bio", ""),
            "slug": a.get("slug", "")
        } for a in authors]
