from typing import List, Optional, Any
from datetime import datetime, timezone
import uuid
import json
import re
from fastapi import HTTPException
from core.database import db_client
from models.user import UserInDB
from models.social import StatusUpdateInDB
from loguru import logger

class PostService:
    @staticmethod
    async def create_post(request, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        user_col = db["users"]
        mention_matches = re.findall(r"@([\w\.]+)", request.content)
        mentions_ids = []
        if mention_matches:
            mentioned_users = await user_col.find({"full_name": {"$in": mention_matches}}).to_list(length=10)
            mentions_ids = [str(u["_id"]) for u in mentioned_users]
            for m_uid in mentions_ids:
                if m_uid != str(current_user.id):
                    await db_client.redis.publish(
                        f"user_notifications:{m_uid}", 
                        json.dumps({
                            "title": "Bạn được nhắc đến", 
                            "body": f"{current_user.full_name} đã nhắc đến bạn.", 
                            "link": "/feed"
                        })
                    )
        tag_matches = re.findall(r"#([\w\.]+)", request.content)
        final_tags = list(set([t.lower() for t in (request.tags or []) + tag_matches]))
        new_post = StatusUpdateInDB(
            user_id=str(current_user.id),
            content=request.content,
            tags=final_tags,
            mentions=mentions_ids,
            privacy=request.privacy or "public",
            comment_privacy=request.comment_privacy or "public",
            attached_document_id=request.attached_document_id,
            attached_document_title=request.attached_document_title,
            media_urls=request.media_urls or [],
            is_premium=request.is_premium,
            price=request.price or 0,
            read_progress=request.read_progress,
            item_type=request.item_type or "post",
            quote_text=request.quote_text,
            bg_color=request.bg_color,
            font_style=request.font_style,
            repost_post_id=request.repost_post_id,
            scheduled_at=request.scheduled_at,
            poll_options=[{"_id": str(uuid.uuid4()), "text": opt, "votes": 0} for opt in request.poll_options] if request.poll_options else [],
            created_at=datetime.now(timezone.utc)
        )
        await db["status_updates"].insert_one(new_post.model_dump(by_alias=True))
        return {"message": "Đã đăng bài thành công.", "post_id": str(new_post.id)}

    @staticmethod
    async def update_post(post_id: str, content: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        post = await db["status_updates"].find_one({"_id": post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Bài viết không tồn tại.")
        if post["user_id"] != str(current_user.id) and current_user.role != "ADMIN":
            raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa bài viết này.")
        
        await db["status_updates"].update_one(
            {"_id": post_id},
            {"$set": {"content": content, "updated_at": datetime.now(timezone.utc)}}
        )
        return {"message": "Đã cập nhật bài viết thành công."}

    @staticmethod
    async def delete_post(post_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        post = await db["status_updates"].find_one({"_id": post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Bài viết không tồn tại.")
        if post["user_id"] != str(current_user.id) and current_user.role != "ADMIN":
            raise HTTPException(status_code=403, detail="Bạn không có quyền xóa bài viết này.")
        
        await db["status_updates"].update_one(
            {"_id": post_id},
            {"$set": {"is_deleted": True, "deleted_at": datetime.now(timezone.utc)}}
        )
        return {"message": "Đã xóa bài viết thành công."}

    @staticmethod
    async def repost_post(post_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        original_post = await db["status_updates"].find_one({"_id": post_id})
        if not original_post:
            raise HTTPException(status_code=404, detail="Bài viết không tồn tại.")
        
        new_post = {
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "content": original_post.get("content"),
            "media_urls": original_post.get("media_urls"),
            "repost_post_id": post_id,
            "item_type": "post",
            "privacy": "public",
            "created_at": datetime.now(timezone.utc)
        }
        await db["status_updates"].insert_one(new_post)
        return {"message": "Đã chia sẻ lại bài viết thành công.", "post_id": new_post["_id"]}

    @staticmethod
    async def toggle_pin_post(post_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        post = await db["status_updates"].find_one({"_id": post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Bài viết không tồn tại.")
        if post["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Bạn không có quyền ghim bài viết này.")
        
        new_pin_status = not post.get("is_pinned", False)
        await db["status_updates"].update_one({"_id": post_id}, {"$set": {"is_pinned": new_pin_status}})
        return {"message": "Đã ghim bài viết." if new_pin_status else "Đã bỏ ghim bài viết.", "is_pinned": new_pin_status}

    @staticmethod
    async def hide_post(post_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["status_updates"].update_one(
            {"_id": post_id},
            {"$addToSet": {"is_hidden_by": str(current_user.id)}}
        )
        return {"message": "Đã ẩn bài viết."}

    @staticmethod
    async def record_post_view(post_id: str):
        db = db_client.mongodb.get_default_database()
        await db["status_updates"].update_one(
            {"_id": post_id},
            {"$inc": {"view_count": 1}}
        )
        return True

    @staticmethod
    async def save_post(post_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        existing = await db["saved_posts"].find_one({"user_id": str(current_user.id), "post_id": post_id})
        if existing:
            await db["saved_posts"].delete_one({"_id": existing["_id"]})
            await db["status_updates"].update_one({"_id": post_id}, {"$pull": {"saved_by": str(current_user.id)}})
            return {"message": "Đã bỏ lưu bài viết thành công.", "saved": False}
        await db["saved_posts"].insert_one({
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "post_id": post_id,
            "created_at": datetime.now(timezone.utc),
        })
        await db["status_updates"].update_one({"_id": post_id}, {"$addToSet": {"saved_by": str(current_user.id)}})
        return {"message": "Đã lưu bài viết vào mục yêu thích.", "saved": True}

    @staticmethod
    async def get_saved_posts(current_user: UserInDB, cursor: str = None, limit: int = 20) -> list:
        db = db_client.mongodb.get_default_database()
        
        match_query = {"user_id": str(current_user.id)}
        if cursor:
            from datetime import datetime
            match_query["created_at"] = {"$lt": datetime.fromisoformat(cursor.replace('Z', '+00:00'))}
            
        pipeline = [
            {"$match": match_query},
            {"$sort": {"created_at": -1}},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "status_updates",
                    "localField": "post_id",
                    "foreignField": "_id",
                    "as": "post"
                }
            },
            {"$unwind": "$post"},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "post.user_id",
                    "foreignField": "_id",
                    "as": "author"
                }
            },
            {"$unwind": {"path": "$author", "preserveNullAndEmptyArrays": True}}
        ]
        
        results = await db["saved_posts"].aggregate(pipeline).to_list(length=limit)
        
        result = []
        for doc in results:
            p = doc["post"]
            author = doc.get("author", {})
            result.append({
                "_id": str(p["_id"]),
                "content": p.get("content", ""),
                "item_type": p.get("item_type", "post"),
                "created_at": p.get("created_at", datetime.now(timezone.utc).isoformat() if isinstance(p.get("created_at"), datetime) else p.get("created_at")),
                "user": {
                    "_id": str(author.get("_id") if author else p["user_id"]),
                    "full_name": author.get("full_name", "Ẩn danh") if author else "Ẩn danh",
                    "avatar_url": author.get("avatar_url") if author else None,
                },
            })
        return result

    @staticmethod
    async def vote_poll(post_id: str, option_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        post = await db["status_updates"].find_one({"_id": post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Bài viết không tồn tại.")
        
        poll_voters = post.get("poll_voters", {})
        if str(current_user.id) in poll_voters:
            raise HTTPException(status_code=400, detail="Bạn đã bình chọn cho bài viết này rồi.")
        
        poll_options = post.get("poll_options", [])
        option_found = False
        for opt in poll_options:
            if opt["id"] == option_id:
                opt["votes"] = opt.get("votes", 0) + 1
                option_found = True
                break
        
        if not option_found:
            raise HTTPException(status_code=400, detail="Lựa chọn không hợp lệ.")
            
        await db["status_updates"].update_one(
            {"_id": post_id},
            {
                "$set": {
                    "poll_options": poll_options,
                    f"poll_voters.{current_user.id}": option_id
                }
            }
        )
        return {"message": "Bình chọn thành công.", "poll_options": poll_options}

    @staticmethod
    async def get_poll_voters(post_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        post = await db["status_updates"].find_one({"_id": post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Bài viết không tồn tại.")
        poll_options = post.get("poll_options", [])
        poll_voters = post.get("poll_voters", {})
        voter_ids = list(poll_voters.keys())
        if not voter_ids:
            return {"options": poll_options, "voters": {}}
        users = await db["users"].find({"_id": {"$in": voter_ids}}, {"full_name": 1, "avatar_url": 1}).to_list(length=200)
        user_map = {str(u["_id"]): {"full_name": u.get("full_name", "Ẩn danh"), "avatar_url": u.get("avatar_url")} for u in users}
        enriched_voters = {}
        for uid, option_idx in poll_voters.items():
            enriched_voters[uid] = {"option_index": option_idx, "user": user_map.get(uid, {"full_name": "Ẩn danh", "avatar_url": None})}
        return {"options": poll_options, "voters": enriched_voters}

    @staticmethod
    async def share_excerpt(data: dict, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": data["document_id"]})
        if not doc: 
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
            
        excerpt_post = {
            "_id": str(uuid.uuid4()), 
            "user_id": str(current_user.id), 
            "content": data.get("caption", ""), 
            "item_type": "excerpt", 
            "excerpt_text": data["text"], 
            "attached_document_id": data["document_id"], 
            "attached_document_title": doc.get("title", ""), 
            "privacy": "public", 
            "created_at": datetime.now(timezone.utc)
        }
        await db["status_updates"].insert_one(excerpt_post)
        return {"message": "Đã chia sẻ trích đoạn.", "post_id": excerpt_post["_id"]}

    @staticmethod
    async def get_posts_by_hashtag(tag: str, cursor: str = None, limit: int = 20, current_user: Optional[UserInDB] = None) -> list:
        db = db_client.mongodb.get_default_database()
        query = {"tags": tag.lower(), "is_shadowbanned": {"$ne": True}, "is_deleted": {"$ne": True}}
        if current_user:
            query["is_hidden_by"] = {"$ne": str(current_user.id)}
            
        if cursor:
            from datetime import datetime
            query["created_at"] = {"$lt": datetime.fromisoformat(cursor.replace('Z', '+00:00'))}
            
        pipeline = [
            {"$match": query},
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
        
        posts = await db["status_updates"].aggregate(pipeline).to_list(length=limit)
        
        result = []
        for p in posts:
            author = p.get("author", {})
            result.append({
                "_id": str(p["_id"]),
                "content": p.get("content", ""),
                "item_type": p.get("item_type", "post"),
                "tags": p.get("tags", []),
                "created_at": p.get("created_at", datetime.now(timezone.utc).isoformat() if isinstance(p.get("created_at"), datetime) else p.get("created_at")),
                "user": {
                    "_id": str(author.get("_id") if author else p["user_id"]),
                    "full_name": author.get("full_name", "Ẩn danh") if author else "Ẩn danh",
                    "avatar_url": author.get("avatar_url") if author else None,
                },
            })
        return result

    @staticmethod
    async def get_social_feed(tab: str, item_type: Optional[str], limit: int, current_user: Optional[UserInDB], cursor: str = None) -> List[dict]:
        db = db_client.mongodb.get_default_database()
        updates_col = db["status_updates"]
        
        exclude_user_ids = []
        if current_user:
            user_doc = await db["users"].find_one({"_id": str(current_user.id)}, {"blocked_users": 1})
            my_blocks = user_doc.get("blocked_users", []) if user_doc else []
            
            blocked_by_cursor = db["users"].find({"blocked_users": str(current_user.id)}, {"_id": 1})
            blocked_by_me_ids = [str(u["_id"]) async for u in blocked_by_cursor]
            
            muted_cursor = db["muted_users"].find({"user_id": str(current_user.id)}, {"muted_id": 1})
            my_mutes = [m["muted_id"] async for m in muted_cursor]
            
            exclude_user_ids = list(set(my_blocks + blocked_by_me_ids + my_mutes))

        query = {
            "is_hidden_by": {"$ne": str(current_user.id) if current_user else "none"}, 
            "is_shadowbanned": {"$ne": True},
            "is_deleted": {"$ne": True}
        }
        
        if exclude_user_ids:
            query["user_id"] = {"$nin": exclude_user_ids}

        if item_type:
            query["item_type"] = item_type
            
        if cursor:
            from datetime import datetime
            query["created_at"] = {"$lt": datetime.fromisoformat(cursor.replace('Z', '+00:00'))}
            
        if tab == "following" and current_user:
            follows_col = db["follows"]
            following_cursor = await follows_col.find({"follower_id": str(current_user.id)}, {"following_id": 1}).to_list(length=5000)
            following_ids = [f["following_id"] for f in following_cursor]
            
            if "user_id" in query:
                effective_following = [fid for fid in following_ids if fid not in exclude_user_ids]
                query["user_id"] = {"$in": effective_following}
            else:
                query["user_id"] = {"$in": following_ids}
                
        elif tab == "foryou":
            if current_user:
                follows_col = db["follows"]
                following_cursor = await follows_col.find({"follower_id": str(current_user.id)}, {"following_id": 1}).to_list(length=5000)
                following_ids = [f["following_id"] for f in following_cursor]
                
                effective_following = [fid for fid in following_ids if fid not in exclude_user_ids]
                
                query["$or"] = [
                    {"privacy": "public"},
                    {"user_id": str(current_user.id)},
                    {"$and": [{"privacy": "friends"}, {"user_id": {"$in": effective_following}}]}
                ]
            else:
                query["privacy"] = "public"

        pipeline = [
            {"$match": query},
            {"$sort": {"created_at": -1}},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user_details"
                }
            },
            {"$unwind": {"path": "$user_details", "preserveNullAndEmptyArrays": True}}
        ]
        
        cursor_res = updates_col.aggregate(pipeline)
        results = await cursor_res.to_list(length=limit)
        
        feed = []
        for doc in results:
            user_doc = doc.get("user_details", {})
            user_info = {
                "_id": str(user_doc.get("_id")) if user_doc else doc["user_id"],
                "full_name": user_doc.get("full_name", "Ẩn danh") if user_doc else "Ẩn danh",
                "avatar_url": user_doc.get("avatar_url") if user_doc else None,
                "role": user_doc.get("role", "READER") if user_doc else "READER"
            }
            item = {
                "_id": str(doc["_id"]),
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
                "created_at": doc.get("created_at", datetime.now(timezone.utc)).isoformat() if isinstance(doc.get("created_at"), datetime) else doc.get("created_at"),
                "reactions": doc.get("reactions", {}),
                "user_reaction": doc.get("reaction_users", {}).get(str(current_user.id)) if current_user else None,
                "is_pinned": doc.get("is_pinned", False),
                "saved": str(current_user.id) in doc.get("saved_by", []) if current_user else False,
                "user": user_info
            }
            feed.append(item)
        return feed
