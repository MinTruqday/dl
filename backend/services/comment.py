from core.database import db_client
from datetime import datetime, timezone
import uuid
from loguru import logger
from fastapi import HTTPException
from typing import List, Optional, Any
from models.user import UserInDB

class CommentService:
    @staticmethod
    async def create_feed_comment(req: Any, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        comment_id = str(uuid.uuid4())
        new_comment = {
            "_id": comment_id,
            "user_id": str(current_user.id),
            "content": req.content,
            "item_id": req.item_id,
            "parent_id": req.parent_id if hasattr(req, "parent_id") else None,
            "created_at": datetime.now(timezone.utc),
            "is_removed": False
        }
        await db["comments"].insert_one(new_comment)
        logger.info(f"Social: User {current_user.id} commented on item {req.item_id}")
        return {"_id": comment_id, "message": "Bình luận thành công."}

    @staticmethod
    async def create_nested_comment(item_id: str, req: Any, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        comment_id = str(uuid.uuid4())
        new_comment = {
            "_id": comment_id,
            "user_id": str(current_user.id),
            "content": req.content,
            "item_id": item_id,
            "parent_id": req.parent_id if hasattr(req, "parent_id") else None,
            "created_at": datetime.now(timezone.utc),
            "is_removed": False
        }
        await db["comments"].insert_one(new_comment)
        return {"_id": comment_id, "message": "Gửi bình luận thành công."}

    @staticmethod
    async def get_nested_comments(item_id: str, current_user: Optional[UserInDB] = None) -> list:
        db = db_client.mongodb.get_default_database()
        
        exclude_ids = []
        if current_user:
            user_doc = await db["users"].find_one({"_id": str(current_user.id)}, {"blocked_users": 1})
            my_blocks = user_doc.get("blocked_users", []) if user_doc else []
            
            blocked_by_cursor = db["users"].find({"blocked_users": str(current_user.id)}, {"_id": 1})
            blocked_by_me_ids = [str(u["_id"]) async for u in blocked_by_cursor]
            
            muted_cursor = db["muted_users"].find({"user_id": str(current_user.id)}, {"muted_id": 1})
            my_mutes = [m["muted_id"] async for m in muted_cursor]
            
            exclude_ids = list(set(my_blocks + blocked_by_me_ids + my_mutes))

        query = {"item_id": item_id, "is_removed": {"$ne": True}}
        if exclude_ids:
            query["user_id"] = {"$nin": exclude_ids}

        pipeline = [
            {"$match": query},
            {"$sort": {"created_at": -1}},
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
        
        comments = await db["comments"].aggregate(pipeline).to_list(length=100)
        return [{
            "_id": c["_id"],
            "content": c["content"],
            "parent_id": c.get("parent_id"),
            "item_id": c.get("item_id"),
            "created_at": c["created_at"].isoformat() if isinstance(c["created_at"], datetime) else c["created_at"],
            "user": {
                "_id": c["user_id"],
                "full_name": c.get("author", {}).get("full_name", "Ẩn danh"),
                "avatar_url": c.get("author", {}).get("avatar_url")
            }
        } for c in comments]

    @staticmethod
    async def edit_comment(comment_id: str, new_content: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        comment = await db["comments"].find_one({"_id": comment_id})
        if not comment:
            raise HTTPException(status_code=404, detail="Bình luận không tồn tại.")
        if comment["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Bạn không có quyền sửa bình luận này.")
        
        await db["comments"].update_one(
            {"_id": comment_id},
            {"$set": {"content": new_content, "updated_at": datetime.now(timezone.utc)}}
        )
        return {"message": "Cập nhật bình luận thành công."}

    @staticmethod
    async def delete_comment(comment_id: str):
        db = db_client.mongodb.get_default_database()
        await db["comments"].delete_one({"_id": comment_id})
        return True

    @staticmethod
    async def bulk_delete_comments(user_id: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["comments"].delete_many({"user_id": user_id})
        await db["audit_logs"].insert_one({
            "action": "BULK_DELETE_COMMENTS", 
            "actor_id": str(current_moderator.id), 
            "target_user_id": user_id, 
            "count": result.deleted_count, 
            "timestamp": datetime.now(timezone.utc)
        })
        logger.info(f"Moderation: Bulk deleted {result.deleted_count} comments from user {user_id} by {current_moderator.id}")
        return {"message": f"Đã xóa {result.deleted_count} bình luận thành công."}

    @staticmethod
    async def remove_violating_comment(comment_id: str, reason: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["comments"].update_one(
            {"_id": comment_id}, 
            {"$set": {"is_removed": True, "removal_reason": reason, "removed_at": datetime.now(timezone.utc)}}
        )
        logger.info(f"Moderation: Violating comment {comment_id} removed by {current_moderator.id} for reason: {reason}")
        return {"message": "Đã gỡ bỏ bình luận vi phạm."}
