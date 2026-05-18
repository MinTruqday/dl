from typing import List, Optional, Any
from datetime import datetime, timezone
import uuid
import json
from fastapi import HTTPException
from core.database import db_client
from models.user import UserInDB
from models.social import FollowInDB
from loguru import logger

class InteractionService:
    @staticmethod
    async def toggle_follow(target_user_id: str, current_user: UserInDB) -> dict:
        if str(current_user.id) == target_user_id:
            raise HTTPException(status_code=400, detail="Bạn không thể tự theo dõi chính mình.")
        db = db_client.mongodb.get_default_database()
        existing = await db["follows"].find_one({"follower_id": str(current_user.id), "following_id": target_user_id})
        if existing:
            await db["follows"].delete_one({"_id": existing["_id"]})
            logger.info(f"Interaction: User {current_user.id} unfollowed {target_user_id}")
            return {"message": "Đã bỏ theo dõi thành công."}
        else:
            await db["follows"].insert_one(FollowInDB(follower_id=str(current_user.id), following_id=target_user_id).model_dump(by_alias=True))
            target_user = await db["users"].find_one({"_id": target_user_id})
            if target_user and target_user.get("welcome_message"):
                welcome_msg = target_user["welcome_message"]
                notif = {
                    "_id": str(uuid.uuid4()),
                    "user_id": str(current_user.id),
                    "title": f"Lời chào từ {target_user.get('full_name', 'Tác giả')}",
                    "message": welcome_msg,
                    "is_read": False,
                    "type": "welcome",
                    "created_at": datetime.now(timezone.utc),
                }
                await db["notifications"].insert_one(notif)
                if db_client.redis:
                    await db_client.redis.publish(
                        f"user_notifications:{current_user.id}", 
                        json.dumps({"title": notif["title"], "body": notif["message"]})
                    )

            await db_client.redis.publish(
                f"user_notifications:{target_user_id}", 
                json.dumps({
                    "title": "Người theo dõi mới", 
                    "body": f"{current_user.full_name} đã bắt đầu theo dõi bạn.", 
                    "link": "/profile"
                })
            )
            logger.info(f"Interaction: User {current_user.id} followed {target_user_id}")
            return {"message": "Đã theo dõi thành công."}

    @staticmethod
    async def react_to_post(post_id: str, reaction_type: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        post = await db["status_updates"].find_one({"_id": post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Bài viết không tồn tại.")
        
        user_id_str = str(current_user.id)
        reaction_users = post.get("reaction_users", {})
        
        if user_id_str in reaction_users:
            old_reaction = reaction_users[user_id_str]
            if old_reaction == reaction_type:
                await db["status_updates"].update_one(
                    {"_id": post_id},
                    {
                        "$inc": {f"reactions.{reaction_type}": -1},
                        "$unset": {f"reaction_users.{user_id_str}": ""}
                    }
                )
                return {"message": "Đã bỏ cảm xúc.", "action": "removed"}
            else:
                await db["status_updates"].update_one(
                    {"_id": post_id},
                    {
                        "$inc": {f"reactions.{old_reaction}": -1, f"reactions.{reaction_type}": 1},
                        "$set": {f"reaction_users.{user_id_str}": reaction_type}
                    }
                )
                return {"message": "Đã thay đổi cảm xúc.", "action": "changed"}
        else:
            await db["status_updates"].update_one(
                {"_id": post_id},
                {
                    "$inc": {f"reactions.{reaction_type}": 1},
                    "$set": {f"reaction_users.{user_id_str}": reaction_type}
                }
            )
            return {"message": "Đã thả cảm xúc.", "action": "added"}

    @staticmethod
    async def report_post(post_id: str, reason: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        report = {
            "_id": str(uuid.uuid4()),
            "target_id": post_id,
            "reporter_id": str(current_user.id),
            "reason": reason,
            "status": "PENDING",
            "created_at": datetime.now(timezone.utc)
        }
        await db["reports"].insert_one(report)
        logger.info(f"Interaction: Post {post_id} reported by {current_user.id}")
        return {"message": "Đã gửi báo cáo vi phạm."}

    @staticmethod
    async def mute_user(target_user_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        if str(current_user.id) == target_user_id:
            raise HTTPException(status_code=400, detail="Không thể tắt tiếng chính mình.")
        existing = await db["muted_users"].find_one({"user_id": str(current_user.id), "muted_id": target_user_id})
        if existing:
            await db["muted_users"].delete_one({"_id": existing["_id"]})
            return {"message": "Đã bỏ tắt tiếng người dùng.", "muted": False}
        await db["muted_users"].insert_one({
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "muted_id": target_user_id,
            "created_at": datetime.now(timezone.utc),
        })
        return {"message": "Đã tắt tiếng người dùng này.", "muted": True}

    @staticmethod
    async def get_muted_users(current_user: UserInDB) -> list:
        db = db_client.mongodb.get_default_database()
        muted = await db["muted_users"].find({"user_id": str(current_user.id)}).to_list(length=100)
        muted_ids = [m["muted_id"] for m in muted]
        if not muted_ids:
            return []
        users = await db["users"].find({"_id": {"$in": muted_ids}}, {"full_name": 1, "avatar_url": 1}).to_list(length=100)
        return [{"id": str(u["_id"]), "full_name": u.get("full_name", "Ẩn danh"), "avatar_url": u.get("avatar_url")} for u in users]

    @staticmethod
    async def block_user(target_user_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        if str(current_user.id) == target_user_id:
            raise HTTPException(status_code=400, detail="Không thể chặn chính mình.")
        
        user_id_str = str(current_user.id)
        await db["users"].update_one(
            {"_id": user_id_str},
            {"$addToSet": {"blocked_users": target_user_id}}
        )
        await db["follows"].delete_many({"$or": [
            {"follower_id": user_id_str, "following_id": target_user_id},
            {"follower_id": target_user_id, "following_id": user_id_str},
        ]})
        logger.info(f"Interaction: User {target_user_id} blocked by {current_user.id}")
        return {"message": "Đã chặn người dùng này thành công.", "blocked": True}

    @staticmethod
    async def unblock_user(target_user_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["users"].update_one(
            {"_id": str(current_user.id)},
            {"$pull": {"blocked_users": target_user_id}}
        )
        return {"message": "Đã bỏ chặn người dùng thành công.", "blocked": False}

    @staticmethod
    async def get_blocked_users(current_user: UserInDB) -> list:
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)}, {"blocked_users": 1})
        blocked_ids = user.get("blocked_users", []) if user else []
        if not blocked_ids:
            return []
        users = await db["users"].find({"_id": {"$in": blocked_ids}}, {"full_name": 1, "avatar_url": 1}).to_list(length=100)
        return [{"id": str(u["_id"]), "full_name": u.get("full_name", "Ẩn danh"), "avatar_url": u.get("avatar_url")} for u in users]

    @staticmethod
    async def get_friend_suggestions_by_intersection(current_user: UserInDB) -> List[dict]:
        db = db_client.mongodb.get_default_database()
        user_col = db["users"]
        follows_col = db["follows"]
        
        following = await follows_col.find({"follower_id": str(current_user.id)}, {"following_id": 1}).to_list(length=5000)
        exclude_ids = [f["following_id"] for f in following] + [str(current_user.id)]
        
        user_doc = await user_col.find_one({"_id": str(current_user.id)}, {"interests": 1})
        user_tags = user_doc.get("interests", []) if user_doc else []
        
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
    async def search_users(query: str, limit: int = 10, current_user: Optional[UserInDB] = None) -> list:
        db = db_client.mongodb.get_default_database()
        
        exclude_ids = []
        if current_user:
            user_doc = await db["users"].find_one({"_id": str(current_user.id)}, {"blocked_users": 1})
            my_blocks = user_doc.get("blocked_users", []) if user_doc else []
            
            blocked_by_cursor = db["users"].find({"blocked_users": str(current_user.id)}, {"_id": 1})
            blocked_by_me_ids = [str(u["_id"]) async for u in blocked_by_cursor]
            
            exclude_ids = list(set(my_blocks + blocked_by_me_ids))

        search_query = {
            "$or": [
                {"full_name": {"$regex": query, "$options": "i"}},
                {"slug": {"$regex": query, "$options": "i"}},
            ],
            "is_active": True,
        }
        
        if exclude_ids:
            search_query["_id"] = {"$nin": exclude_ids}

        users = await db["users"].find(
            search_query, 
            {"full_name": 1, "slug": 1, "avatar_url": 1, "role": 1}
        ).limit(limit).to_list(length=limit)
        
        return [{
            "id": str(u["_id"]),
            "full_name": u.get("full_name", "Ẩn danh"),
            "slug": u.get("slug", ""),
            "avatar_url": u.get("avatar_url"),
            "role": u.get("role", "READER"),
        } for u in users]
