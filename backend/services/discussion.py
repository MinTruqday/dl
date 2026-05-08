from typing import List, Optional, Any
from datetime import datetime, timezone
import uuid
from fastapi import HTTPException
from core.database import db_client
from loguru import logger

class DiscussionService:
    @staticmethod
    async def create_discussion(document_id: str, data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
        discussion = {
            "_id": str(uuid.uuid4()),
            "document_id": document_id,
            "user_id": str(current_user.id),
            "title": data["title"],
            "content": data["content"],
            "replies": [],
            "created_at": datetime.now(timezone.utc),
        }
        await db["discussions"].insert_one(discussion)
        logger.info(f"Discussion: New topic created for document {document_id} by {current_user.id}")
        return {"message": "Tạo thảo luận thành công.", "discussion_id": discussion["_id"]}

    @staticmethod
    async def get_discussions(document_id: str, cursor: str = None, limit: int = 20, current_user: Optional[Any] = None) -> list:
        db = db_client.mongodb.get_default_database()
        
        exclude_ids = []
        if current_user:
            # 1. Get users I blocked
            user_doc = await db["users"].find_one({"_id": str(current_user.id)}, {"blocked_users": 1})
            my_blocks = user_doc.get("blocked_users", []) if user_doc else []
            
            # 2. Get users who blocked me
            blocked_by_cursor = db["users"].find({"blocked_users": str(current_user.id)}, {"_id": 1})
            blocked_by_me_ids = [str(u["_id"]) async for u in blocked_by_cursor]
            
            # 3. Get users I muted
            muted_cursor = db["muted_users"].find({"user_id": str(current_user.id)}, {"muted_id": 1})
            my_mutes = [m["muted_id"] async for m in muted_cursor]
            
            exclude_ids = list(set(my_blocks + blocked_by_me_ids + my_mutes))

        match_query = {"document_id": document_id}
        if exclude_ids:
            match_query["user_id"] = {"$nin": exclude_ids}

        if cursor:
            match_query["created_at"] = {"$lt": datetime.fromisoformat(cursor.replace('Z', '+00:00'))}

        pipeline = [
            {"$match": match_query},
            {"$sort": {"created_at": -1}},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "author"
                }
            },
            {"$unwind": {"path": "$author", "preserveNullAndEmptyArrays": True}}
        ]
        discussions = await db["discussions"].aggregate(pipeline).to_list(length=limit)
        result = []
        for d in discussions:
            author = d.get("author", {})
            # Filter replies from blocked users
            all_replies = d.get("replies", [])
            filtered_replies = [r for r in all_replies if r.get("user_id") not in exclude_ids]
            
            result.append({
                "id": d["_id"],
                "title": d.get("title", ""),
                "content": d.get("content", ""),
                "user_name": author.get("full_name", "Ẩn danh") if author else "Ẩn danh",
                "user_avatar": author.get("avatar_url") if author else None,
                "replies_count": len(filtered_replies),
                "created_at": d["created_at"].isoformat() if isinstance(d.get("created_at"), datetime) else d.get("created_at"),
            })
        return result

    @staticmethod
    async def reply_discussion(discussion_id: str, data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        reply = {
            "id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "content": data["content"],
            "created_at": datetime.now(timezone.utc),
        }
        result = await db["discussions"].update_one(
            {"_id": discussion_id},
            {"$push": {"replies": reply}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Thảo luận không tồn tại.")
        return {"message": "Đã trả lời thành công."}
