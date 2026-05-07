from typing import List, Optional, Any
from datetime import datetime
import httpx
from fastapi import HTTPException
from core.database import db_client
from models.user import UserInDB
from core.config import settings
from loguru import logger

class SocialFeedService:
    @staticmethod
    async def generate_ai_feed_summary(current_user: UserInDB) -> str:
        feed = await SocialFeedService.get_social_feed("foryou", None, 0, 10, current_user)
        if not feed:
            return "Chưa có nội dung mới nào để tóm tắt."
        
        texts = [f"{item['user']['full_name']}: {item['content']}" for item in feed if item.get('content')]
        combined_text = "\n".join(texts)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{settings.AGENTIC_RAG_URL}/inference/summarize",
                    json={"text": combined_text, "language": "vi"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("summary", "Không thể tạo tóm tắt vào lúc này.")
        except Exception as e:
            logger.error(f"Lỗi tóm tắt AI: {str(e)}")
            
        return "Dịch vụ AI hiện đang bận, vui lòng thử lại sau."

    @staticmethod
    async def get_social_feed(tab: str, item_type: Optional[str], skip: int, limit: int, current_user: Optional[UserInDB]) -> List[dict]:
        db = db_client.mongodb.get_default_database()
        updates_col = db["status_updates"]
        users_col = db["users"]
        query = {"is_hidden_by": {"$ne": str(current_user.id) if current_user else "none"}, "is_shadowbanned": {"$ne": True}}
        if item_type:
            query["item_type"] = item_type
        if tab == "following" and current_user:
            follows_col = db["follows"]
            following_cursor = await follows_col.find({"follower_id": str(current_user.id)}).to_list(length=None)
            following_ids = [f["following_id"] for f in following_cursor]
            query["user_id"] = {"$in": following_ids}
        elif tab == "foryou":
            if current_user:
                follows_col = db["follows"]
                following_cursor = await follows_col.find({"follower_id": str(current_user.id)}).to_list(length=None)
                following_ids = [f["following_id"] for f in following_cursor]
                query["$or"] = [
                    {"privacy": "public"},
                    {"user_id": str(current_user.id)},
                    {"$and": [{"privacy": "friends"}, {"user_id": {"$in": following_ids}}]}
                ]
            else:
                query["privacy"] = "public"
        
        cursor = await updates_col.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        feed = []
        for doc in cursor:
            user_doc = await users_col.find_one({"_id": doc["user_id"]})
            user_info = {
                "id": str(user_doc["_id"]) if user_doc else doc["user_id"],
                "full_name": user_doc.get("full_name", "Ẩn danh") if user_doc else "Ẩn danh",
                "avatar_url": user_doc.get("avatar_url") if user_doc else None,
                "role": user_doc.get("role", "READER") if user_doc else "READER"
            }
            item = {
                "id": str(doc["_id"]),
                "user_id": doc["user_id"],
                "content": doc.get("content", ""),
                "item_type": doc.get("item_type", "post"),
                "media_urls": doc.get("media_urls", []),
                "poll_options": doc.get("poll_options", []),
                "attached_document_id": doc.get("attached_document_id"),
                "attached_document_title": doc.get("attached_document_title"),
                "is_premium": doc.get("is_premium", False),
                "price": doc.get("price", 0),
                "read_progress": doc.get("read_progress"),
                "quote_text": doc.get("quote_text"),
                "bg_color": doc.get("bg_color"),
                "font_style": doc.get("font_style"),
                "created_at": doc.get("created_at", datetime.utcnow()).isoformat() if isinstance(doc.get("created_at"), datetime) else doc.get("created_at"),
                "reactions": doc.get("reactions", {}),
                "user_reaction": doc.get("reaction_users", {}).get(str(current_user.id)) if current_user else None,
                "is_pinned": doc.get("is_pinned", False),
                "saved": str(current_user.id) in doc.get("saved_by", []) if current_user else False,
                "user": user_info
            }
            feed.append(item)
        return feed

    @staticmethod
    async def get_friend_suggestions_by_intersection(current_user: UserInDB) -> List[dict]:
        db = db_client.mongodb.get_default_database()
        user_col = db["users"]
        follows_col = db["follows"]
        
        following = await follows_col.find({"follower_id": str(current_user.id)}).to_list(length=None)
        exclude_ids = [f["following_id"] for f in following] + [str(current_user.id)]
        
        user_tags = current_user.interests if hasattr(current_user, 'interests') else []
        
        pipeline = [
            {"$match": {"_id": {"$nin": exclude_ids}, "is_active": True}},
            {"$addFields": {
                "total_match": {
                    "$size": {
                        "$setIntersection": [
                            {"$ifNull": ["$interests", []]}, 
                            user_tags
                        ]
                    }
                }
            }},
            {"$sort": {"total_match": -1}},
            {"$limit": 5},
            {"$project": {"_id": 1, "full_name": 1, "avatar_url": 1, "bio": 1, "role": 1, "total_match": 1}}
        ]
        
        suggestions_cursor = await user_col.aggregate(pipeline).to_list(length=5)
        suggestions = []
        for doc in suggestions_cursor:
            suggestions.append({
                "id": str(doc["_id"]),
                "full_name": doc.get("full_name", "Người dùng"),
                "avatar_url": doc.get("avatar_url"),
                "bio": doc.get("bio"),
                "total_match": doc.get("total_match", 0),
                "role": doc.get("role", "READER")
            })
        return suggestions

    @staticmethod
    async def get_trending_tags(limit: int = 10) -> List[str]:
        db = db_client.mongodb.get_default_database()
        docs_col = db["documents"]
        pipeline = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        results = await docs_col.aggregate(pipeline).to_list(length=limit)
        return [r["_id"] for r in results]

    @staticmethod
    async def get_suggested_documents(limit: int = 5) -> List[dict]:
        db = db_client.mongodb.get_default_database()
        docs_col = db["documents"]
        cursor = docs_col.find({"status": "published"}).sort("views", -1).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [{
            "id": str(b["_id"]),
            "slug": b.get("slug"),
            "title": b.get("title"),
            "author": b.get("author", "Unknown"),
            "cover_url": b.get("cover_url"),
            "mentions": b.get("views", 0),
            "average_rating": b.get("average_rating", 0)
        } for b in documents]

    @staticmethod
    async def search_users(query: str, limit: int = 10) -> list:
        db = db_client.mongodb.get_default_database()
        users = await db["users"].find({
            "$or": [
                {"full_name": {"$regex": query, "$options": "i"}},
                {"slug": {"$regex": query, "$options": "i"}},
            ],
            "is_active": True,
        }, {"full_name": 1, "slug": 1, "avatar_url": 1, "role": 1}).limit(limit).to_list(length=limit)
        return [{
            "id": str(u["_id"]),
            "full_name": u.get("full_name", "Ẩn danh"),
            "slug": u.get("slug", ""),
            "avatar_url": u.get("avatar_url"),
            "role": u.get("role", "READER"),
        } for u in users]
