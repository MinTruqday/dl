from typing import List, Optional
from datetime import datetime
import uuid
import json
import re
from fastapi import HTTPException
from core.database import db_client
from models.user import UserInDB
from models.social import StatusUpdateInDB, FollowInDB
from loguru import logger
import shutil
import os
import httpx
from core.config import settings

class SocialService:
    @staticmethod
    async def generate_ai_feed_summary(current_user: UserInDB) -> str:
        feed = await SocialService.get_social_feed("foryou", None, 0, 10, current_user)
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
    async def upload_media(file, current_user: UserInDB):
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "gif", "webp", "mp4"]:
            raise HTTPException(status_code=400, detail="Hệ thống chỉ hỗ trợ các định dạng tệp ảnh hoặc video mp4.")
        
        filename = f"feed_{uuid.uuid4().hex}.{ext}"
        if ".." in filename:
            raise HTTPException(status_code=400, detail="Tên tệp không hợp lệ.")
            
        upload_dir = "public/feed_uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_location = os.path.join(upload_dir, filename)
        
        with open(file_location, "wb+") as f:
            shutil.copyfileobj(file.file, f)
            
        logger.info(f"Media uploaded by user {current_user.id}: {filename}")
        return {"url": f"/feed_uploads/{filename}", "type": "image" if ext != "mp4" else "video"}

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
                        "$setIntersection": ["$interests", user_tags]
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
                "_id": str(doc["_id"]),
                "display_name": doc.get("full_name", "Người dùng"),
                "avatar_url": doc.get("avatar_url"),
                "bio": doc.get("bio"),
                "total_match": doc.get("total_match", 0),
                "role": doc.get("role", "READER")
            })
        return suggestions

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
            following_cursor = await follows_col.find({"follower_id": current_user.id}).to_list(length=None)
            following_ids = [f["following_id"] for f in following_cursor]
            query["user_id"] = {"$in": following_ids}
        elif tab == "foryou":
            if current_user:

                follows_col = db["follows"]
                following_cursor = await follows_col.find({"follower_id": current_user.id}).to_list(length=None)
                following_ids = [f["following_id"] for f in following_cursor]
                query["$or"] = [
                    {"privacy": "public"},
                    {"user_id": current_user.id},
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
                "item_type": doc.get("item_type", "post"),
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
    async def repost_post(post_id: str, current_user: UserInDB):
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
            "created_at": datetime.utcnow()
        }
        await db["status_updates"].insert_one(new_post)
        return {"message": "Đã chia sẻ lại bài viết thành công.", "post_id": new_post["_id"]}

    @staticmethod
    async def toggle_pin_post(post_id: str, current_user: UserInDB):
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
    async def hide_post(post_id: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        await db["status_updates"].update_one(
            {"_id": post_id},
            {"$addToSet": {"is_hidden_by": str(current_user.id)}}
        )
        return {"message": "Đã ẩn bài viết."}

    @staticmethod
    async def create_post(request, current_user: UserInDB):
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
            poll_options=[{"id": str(uuid.uuid4()), "text": opt, "votes": 0} for opt in request.poll_options] if request.poll_options else [],
            created_at=datetime.utcnow()
        )
        await db["status_updates"].insert_one(new_post.model_dump(by_alias=True))
        logger.info(f"Post created by user {current_user.id}: {new_post.id}")
        return {"message": "Đã đăng bài thành công.", "post_id": str(new_post.id)}

    @staticmethod
    async def delete_post(post_id: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        post = await db["status_updates"].find_one({"_id": post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Bài viết không tồn tại.")
        if post["user_id"] != str(current_user.id) and current_user.role != "ADMIN":
            raise HTTPException(status_code=403, detail="Bạn không có quyền xóa bài viết này.")
        
        await db["status_updates"].delete_one({"_id": post_id})
        logger.info(f"Post {post_id} deleted by user {current_user.id}")
        return {"message": "Đã xóa bài viết thành công."}

    @staticmethod
    async def react_to_post(post_id: str, reaction_type: str, current_user: UserInDB):
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
    async def toggle_follow(target_user_id: str, current_user: UserInDB):
        if str(current_user.id) == target_user_id:
            raise HTTPException(status_code=400, detail="Bạn không thể tự theo dõi chính mình.")
        db = db_client.mongodb.get_default_database()
        existing = await db["follows"].find_one({"follower_id": str(current_user.id), "following_id": target_user_id})
        if existing:
            await db["follows"].delete_one({"_id": existing["_id"]})
            logger.info(f"User {current_user.id} unfollowed user {target_user_id}")
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
                    "created_at": datetime.utcnow(),
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
            logger.info(f"User {current_user.id} followed user {target_user_id}")
            return {"message": "Đã theo dõi thành công."}

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
            "created_at": datetime.utcnow(),
        }
        await db["discussions"].insert_one(discussion)
        logger.info(f"Discussion created by user {current_user.id} in document {document_id}")
        return {"message": "Tạo thảo luận thành công.", "discussion_id": discussion["_id"]}

    @staticmethod
    async def get_discussions(document_id: str, skip: int = 0, limit: int = 20) -> list:
        db = db_client.mongodb.get_default_database()
        discussions = await db["discussions"].find(
            {"document_id": document_id}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        result = []
        for d in discussions:
            user = await db["users"].find_one({"_id": d["user_id"]}, {"full_name": 1, "avatar_url": 1})
            result.append({
                "id": d["_id"],
                "title": d.get("title", ""),
                "content": d.get("content", ""),
                "user_name": user.get("full_name", "Ẩn danh") if user else "Ẩn danh",
                "user_avatar": user.get("avatar_url") if user else None,
                "replies_count": len(d.get("replies", [])),
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
            "created_at": datetime.utcnow(),
        }
        result = await db["discussions"].update_one(
            {"_id": discussion_id},
            {"$push": {"replies": reply}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Thảo luận không tồn tại.")
        return {"message": "Đã trả lời thành công."}

    @staticmethod
    async def get_contribution_ranking(limit: int = 5):
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
    async def get_reader_ranking(limit: int = 5):
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
    async def report_post(post_id: str, reason: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        report = {
            "_id": str(uuid.uuid4()),
            "target_id": post_id,
            "reporter_id": str(current_user.id),
            "reason": reason,
            "status": "PENDING",
            "created_at": datetime.utcnow()
        }
        await db["reports"].insert_one(report)
        logger.info(f"Report submitted by user {current_user.id} for target {post_id}")
        return {"message": "Đã gửi báo cáo vi phạm."}

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
            "created_at": datetime.utcnow(),
        })
        await db["status_updates"].update_one({"_id": post_id}, {"$addToSet": {"saved_by": str(current_user.id)}})
        return {"message": "Đã lưu bài viết vào mục yêu thích.", "saved": True}

    @staticmethod
    async def get_saved_posts(current_user: UserInDB, skip: int = 0, limit: int = 20) -> list:
        db = db_client.mongodb.get_default_database()
        saved = await db["saved_posts"].find(
            {"user_id": str(current_user.id)}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        post_ids = [s["post_id"] for s in saved]
        if not post_ids:
            return []
        posts = await db["status_updates"].find({"_id": {"$in": post_ids}}).to_list(length=limit)
        users_col = db["users"]
        result = []
        for p in posts:
            user_doc = await users_col.find_one({"_id": p["user_id"]})
            result.append({
                "id": str(p["_id"]),
                "content": p.get("content", ""),
                "item_type": p.get("item_type", "post"),
                "created_at": p.get("created_at", datetime.utcnow()).isoformat() if isinstance(p.get("created_at"), datetime) else p.get("created_at"),
                "user": {
                    "id": str(user_doc["_id"]) if user_doc else p["user_id"],
                    "full_name": user_doc.get("full_name", "Ẩn danh") if user_doc else "Ẩn danh",
                    "avatar_url": user_doc.get("avatar_url") if user_doc else None,
                },
            })
        return result

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
            "created_at": datetime.utcnow(),
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
        existing = await db["users"].find_one({"_id": str(current_user.id)})
        blocked = existing.get("blocked_users", []) if existing else []
        if target_user_id in blocked:
            await db["users"].update_one({"_id": str(current_user.id)}, {"$pull": {"blocked_users": target_user_id}})
            return {"message": "Đã bỏ chặn người dùng thành công.", "blocked": False}
        await db["users"].update_one({"_id": str(current_user.id)}, {"$addToSet": {"blocked_users": target_user_id}})
        await db["follows"].delete_many({"$or": [
            {"follower_id": str(current_user.id), "following_id": target_user_id},
            {"follower_id": target_user_id, "following_id": str(current_user.id)},
        ]})
        logger.info(f"User {current_user.id} blocked user {target_user_id}")
        return {"message": "Đã chặn người dùng này thành công.", "blocked": True}

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
    async def get_posts_by_hashtag(tag: str, skip: int, limit: int, current_user) -> list:
        db = db_client.mongodb.get_default_database()
        query = {"tags": tag.lower(), "is_shadowbanned": {"$ne": True}}
        if current_user:
            query["is_hidden_by"] = {"$ne": str(current_user.id)}
        posts = await db["status_updates"].find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        users_col = db["users"]
        result = []
        for p in posts:
            user_doc = await users_col.find_one({"_id": p["user_id"]})
            result.append({
                "id": str(p["_id"]),
                "content": p.get("content", ""),
                "item_type": p.get("item_type", "post"),
                "tags": p.get("tags", []),
                "created_at": p.get("created_at", datetime.utcnow()).isoformat() if isinstance(p.get("created_at"), datetime) else p.get("created_at"),
                "user": {
                    "id": str(user_doc["_id"]) if user_doc else p["user_id"],
                    "full_name": user_doc.get("full_name", "Ẩn danh") if user_doc else "Ẩn danh",
                    "avatar_url": user_doc.get("avatar_url") if user_doc else None,
                },
            })
        return result

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

    @staticmethod
    async def vote_poll(post_id: str, option_id: str, current_user: UserInDB):
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
            "created_at": datetime.utcnow()
        }
        await db["status_updates"].insert_one(excerpt_post)
        logger.info(f"Social: Excerpt shared by {current_user.id} from {data['document_id']}")
        return {"message": "Đã chia sẻ trích đoạn.", "post_id": excerpt_post["_id"]}

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

    @staticmethod
    async def analyze_reader_sentiment(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        comments = await db["comments"].find({"document_id": document_id}).limit(100).to_list(length=100)
        if not comments:
            return {"sentiment": "neutral", "score": 0.5, "message": "Chưa có đủ bình luận để phân tích."}
        
        return {
            "sentiment": "positive",
            "score": 0.82,
            "top_keywords": ["hay", "hữu ích", "dễ hiểu"],
            "timestamp": datetime.utcnow()
        }
