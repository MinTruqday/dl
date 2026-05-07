from core.database import db_client
from datetime import datetime
import uuid
from loguru import logger

class CommentService:
    @staticmethod
    async def bulk_delete_comments(user_id: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["comments"].delete_many({"user_id": user_id})
        await db["audit_logs"].insert_one({
            "action": "BULK_DELETE_COMMENTS", 
            "actor_id": str(current_moderator.id), 
            "target_user_id": user_id, 
            "count": result.deleted_count, 
            "timestamp": datetime.utcnow()
        })
        logger.info(f"Moderation: {result.deleted_count} comments deleted for user {user_id} by {current_moderator.id}")
        return {"message": f"Đã xóa {result.deleted_count} bình luận thành công."}

    @staticmethod
    async def remove_violating_comment(comment_id: str, reason: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["comments"].update_one(
            {"_id": comment_id}, 
            {"$set": {"is_removed": True, "removal_reason": reason, "removed_at": datetime.utcnow()}}
        )
        logger.info(f"Moderation: Comment {comment_id} removed by {current_moderator.id}")
        return {"message": "Đã gỡ bỏ bình luận vi phạm."}
