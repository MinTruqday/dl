from core.database import db_client
from fastapi import HTTPException
from datetime import datetime
import uuid
from loguru import logger

class GuestService:
    @staticmethod
    async def get_featured_authors(limit: int = 10) -> list:
        db = db_client.mongodb.get_default_database()
        pipeline = [
            {"$match": {"role": "AUTHOR", "is_active": True}},
            {"$lookup": {"from": "documents", "localField": "_id", "foreignField": "author_id", "as": "documents"}},
            {"$addFields": {"document_count": {"$size": "$documents"}, "total_views": {"$sum": "$documents.views"}}},
            {"$sort": {"total_views": -1}}, {"$limit": limit},
            {"$project": {"_id": 1, "full_name": 1, "slug": 1, "avatar_url": 1, "bio": 1, "document_count": 1, "total_views": 1}}
        ]
        authors = await db["users"].aggregate(pipeline).to_list(length=limit)
        return [{"id": str(a["_id"]), "full_name": a.get("full_name", "Ẩn danh"), "slug": a.get("slug", ""), "avatar_url": a.get("avatar_url"), "bio": a.get("bio", ""), "document_count": a.get("document_count", 0), "total_views": a.get("total_views", 0)} for a in authors]

    @staticmethod
    async def get_author_public_profile(author_slug: str) -> dict:
        db = db_client.mongodb.get_default_database()
        author = await db["users"].find_one({"slug": author_slug, "is_active": True})
        if not author: raise HTTPException(status_code=404, detail="Tác giả không tồn tại.")
        documents = await db["documents"].find({"author_id": str(author["_id"]), "status": "published"}).sort("created_at", -1).to_list(length=50)
        followers_count = await db["follows"].count_documents({"following_id": str(author["_id"])})
        return {
            "id": str(author["_id"]), "full_name": author.get("full_name", "Ẩn danh"), "slug": author.get("slug", ""), "avatar_url": author.get("avatar_url"),
            "bio": author.get("bio", ""), "role": author.get("role", "reader"), "followers_count": followers_count,
            "documents": [{"id": str(b["_id"]), "title": b.get("title", ""), "slug": b.get("slug", ""), "cover_url": b.get("cover_url"), "average_rating": b.get("average_rating"), "views": b.get("views", 0)} for b in documents]
        }

    @staticmethod
    async def subscribe_newsletter(email: str) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["newsletter_subs"].update_one({"email": email}, {"$set": {"is_active": True, "updated_at": datetime.utcnow()}}, upsert=True)
        return {"message": "Đã đăng ký nhận tin bản tin."}

    @staticmethod
    async def get_system_notices() -> list:
        db = db_client.mongodb.get_default_database()
        notices = await db["system_notices"].find({"is_active": True}).sort("created_at", -1).to_list(length=10)
        return [{"id": str(n["_id"]), "title": n.get("title"), "content": n.get("content"), "created_at": n["created_at"].isoformat() if isinstance(n.get("created_at"), datetime) else ""} for n in notices]
