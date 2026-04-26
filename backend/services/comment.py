from datetime import datetime
from typing import List, Any, Optional
from fastapi import HTTPException
from core.database import db_client
from models.comment import CommentInDB, CommentResponse
from models.user import RoleEnum
import json
from loguru import logger

class CommentService:
    @staticmethod
    async def create_feed_comment(req, current_user):
        db = db_client.mongodb.get_default_database()
        base_path = ","
        parent_author_id = None
        
        if req.item_type == "post":
            post_doc = await db["status_updates"].find_one({"_id": req.item_id})
            if not post_doc:
                raise HTTPException(status_code=404, detail="Bài viết không tồn tại.")
            privacy = post_doc.get("comment_privacy", "public")
            if privacy == "private" and post_doc.get("user_id") != str(current_user.id):
                raise HTTPException(status_code=403, detail="Chủ bài viết đã tắt bình luận.")
            elif privacy == "followers" and post_doc.get("user_id") != str(current_user.id):
                is_follower = await db["follows"].find_one({"follower_id": str(current_user.id), "following_id": post_doc.get("user_id")})
                if not is_follower:
                    raise HTTPException(status_code=403, detail="Chỉ người theo dõi mới được bình luận.")

        if req.parent_id:
            parent_comment = await db["comments"].find_one({"_id": req.parent_id})
            if not parent_comment:
                raise HTTPException(status_code=404, detail="Bình luận không tồn tại.")
            base_path = parent_comment.get("path", ",") + f"{req.parent_id},"
            parent_author_id = parent_comment.get("user_id")
        
        comment_doc = CommentInDB(
            item_id=req.item_id,
            item_type=req.item_type,
            text=req.content,
            parent_id=req.parent_id,
            path=base_path,
            user_id=str(current_user.id),
        )
        await db["comments"].insert_one(comment_doc.model_dump(by_alias=True))
        logger.info(f"Comment created by user {current_user.id} on {req.item_type} {req.item_id}")
        
        if req.item_type == "post":
            post_doc = await db["status_updates"].find_one({"_id": req.item_id})
            if post_doc and post_doc.get("user_id") and post_doc.get("user_id") != str(current_user.id):
                await db_client.redis.publish(
                    f"user_notifications:{post_doc.get('user_id')}",
                    json.dumps({
                        "title": "Bình luận mới", 
                        "body": f"{getattr(current_user, 'full_name', 'Ai đó')} đã bình luận vào bài viết của bạn.", 
                        "link": f"/feed#post.{req.item_id}"
                    })
                )
        if parent_author_id and parent_author_id != str(current_user.id):
            await db_client.redis.publish(
                f"user_notifications:{parent_author_id}",
                json.dumps({
                    "title": "Phản hồi bình luận", 
                    "body": f"{getattr(current_user, 'full_name', 'Ai đó')} đã phản hồi bình luận của bạn.", 
                    "link": f"/feed#post.{req.item_id}"
                })
            )
        
        response_data = comment_doc.model_dump(by_alias=True)
        response_data["user"] = {
            "id": str(current_user.id), 
            "full_name": getattr(current_user, "full_name", "Anonymous"), 
            "avatar_url": getattr(current_user, "avatar_url", None)
        }
        return CommentResponse(**response_data)

    @staticmethod
    async def create_nested_comment(item_id, comment_in, current_user):
        db = db_client.mongodb.get_default_database()
        base_path = ","
        if comment_in.parent_id:
            parent_comment = await db["comments"].find_one({"_id": comment_in.parent_id})
            if not parent_comment:
                raise HTTPException(status_code=404, detail="Bình luận cha không tồn tại.")
            base_path = parent_comment.get("path", ",") + f"{comment_in.parent_id},"
        
        comment_dict = comment_in.model_dump()
        comment_dict["item_id"] = item_id
        comment_dict["is_shadowbanned_content"] = getattr(current_user, "is_shadowbanned", False)
        comment_dict["path"] = base_path
        comment_doc = CommentInDB(**comment_dict, user_id=str(current_user.id))
        await db["comments"].insert_one(comment_doc.model_dump(by_alias=True))
        logger.info(f"Nested comment created by user {current_user.id} on item {item_id}")
        
        response_data = comment_doc.model_dump(by_alias=True)
        response_data["user"] = {
            "id": str(current_user.id), 
            "full_name": current_user.full_name, 
            "avatar_url": current_user.avatar_url
        }
        return CommentResponse(**response_data)

    @staticmethod
    async def get_nested_comments(item_id, current_user):
        db = db_client.mongodb.get_default_database()
        query = {"item_id": item_id}
        if not (current_user and getattr(current_user, "role", "") == RoleEnum.ADMIN):
            user_id = str(current_user.id) if current_user else "anonymous"
            query["$or"] = [{"is_shadowbanned_content": False}, {"user_id": user_id}]
            
        comments_cursor = db["comments"].find(query).sort([("path", 1), ("created_at", 1)])
        comments = await comments_cursor.to_list(length=1000)
        
        user_ids = list(set([c["user_id"] for c in comments]))
        users_cursor = await db["users"].find({"_id": {"$in": user_ids}}).to_list(length=1000)
        user_map = {u["_id"]: u for u in users_cursor}
        
        results = []
        for c in comments:
            u = user_map.get(c["user_id"], {})
            c["user"] = {
                "id": u.get("_id"), 
                "full_name": u.get("full_name", "Anonymous"), 
                "avatar_url": u.get("avatar_url")
            }
            results.append(CommentResponse(**c))
        return results

    @staticmethod
    async def delete_comment(comment_id):
        db = db_client.mongodb.get_default_database()
        res = await db["comments"].delete_one({"_id": comment_id})
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy bình luận yêu cầu.")
        logger.info(f"Comment {comment_id} deleted")
        return True

    @staticmethod
    async def edit_comment(comment_id: str, new_content: str, current_user):
        from datetime import timedelta
        db = db_client.mongodb.get_default_database()
        comment = await db["comments"].find_one({"_id": comment_id})
        if not comment:
            raise HTTPException(status_code=404, detail="Bình luận không tồn tại.")
        if comment.get("user_id") != str(current_user.id):
            raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa bình luận này.")
        created_at = comment.get("created_at")
        if isinstance(created_at, datetime) and datetime.utcnow() - created_at > timedelta(minutes=15):
            raise HTTPException(status_code=400, detail="Chỉ có thể chỉnh sửa bình luận trong vòng 15 phút sau khi đăng.")
        await db["comments"].update_one(
            {"_id": comment_id},
            {"$set": {"text": new_content, "is_edited": True, "edited_at": datetime.utcnow()}}
        )
        logger.info(f"Comment {comment_id} edited by user {current_user.id}")
        return {"message": "Đã chỉnh sửa bình luận thành công."}

