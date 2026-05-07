from datetime import datetime, timezone, timedelta
import json
import uuid
from typing import Optional
from fastapi import HTTPException
from bson import ObjectId
from core.database import db_client
from models.user import UserInDB
from models.social import StoryCreate, StoryInDB
from loguru import logger


class StoryService:
    @staticmethod
    async def create_story(request: StoryCreate, current_user: UserInDB) -> dict:
        if not request.text_content and not request.media_url:
            raise HTTPException(status_code=400, detail="Tin cần có nội dung hoặc ảnh đính kèm.")
        db = db_client.mongodb.get_default_database()
        story = StoryInDB(
            user_id=str(current_user.id),
            media_url=request.media_url,
            text_content=request.text_content,
            background_color=request.background_color,
            font_style=request.font_style,
            text_color=request.text_color,
            stickers=request.stickers or [],
            privacy=request.privacy,
            link_url=request.link_url,
            link_text=request.link_text,
            poll_data=request.poll_data,
            quiz_data=request.quiz_data,
            mentions=request.mentions or [],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        await db["stories"].insert_one(story.model_dump(by_alias=True))
logger.info("Log message sanitized"))
        return {"message": "Đã đăng tin thành công.", "story_id": str(story.id)}

    @staticmethod
    async def list_stories(current_user: Optional[UserInDB]) -> dict:
        db = db_client.mongodb.get_default_database()
        now = datetime.now(timezone.utc)
        query = {"expires_at": {"$gt": now}, "is_archived": False, "privacy": "public"}
        cursor = db["stories"].find(query).sort("created_at", -1)
        stories_raw = await cursor.to_list(length=50)
        stories = []
        for s in stories_raw:
            user = await db["users"].find_one({"_id": s["user_id"]}, {"full_name": 1, "avatar_url": 1})
            viewer_ids = [v["user_id"] for v in s.get("viewers", [])]
            stories.append({
                "id": str(s["_id"]),
                "user_id": s["user_id"],
                "text_content": s.get("text_content"),
                "media_url": s.get("media_url"),
                "background_color": s.get("background_color", "#18181b"),
                "text_color": s.get("text_color", "#ffffff"),
                "font_style": s.get("font_style", "sans"),
                "link_url": s.get("link_url"),
                "privacy": s.get("privacy", "public"),
                "poll_data": s.get("poll_data"),
                "quiz_data": s.get("quiz_data"),
                "reactions": s.get("reactions", {}),
                "viewer_count": len(viewer_ids),
                "has_unread": str(current_user.id) not in viewer_ids if current_user else True,
                "created_at": s["created_at"].isoformat() if isinstance(s.get("created_at"), datetime) else s.get("created_at"),
                "expires_at": s["expires_at"].isoformat() if isinstance(s.get("expires_at"), datetime) else s.get("expires_at"),
                "user": {
                    "id": s["user_id"],
                    "name": user.get("full_name", "Ẩn danh") if user else "Ẩn danh",
                    "avatar_url": user.get("avatar_url") if user else None,
                },
            })
        return {"stories": stories}

    @staticmethod
    async def get_my_stories(current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        now = datetime.now(timezone.utc)
        cursor = db["stories"].find(
            {"user_id": str(current_user.id), "expires_at": {"$gt": now}, "is_archived": False}
        ).sort("created_at", -1)
        stories_raw = await cursor.to_list(length=50)
        stories = []
        for s in stories_raw:
            viewers_enriched = []
            for v in s.get("viewers", []):
                viewer_user = await db["users"].find_one({"_id": v["user_id"]}, {"full_name": 1, "avatar_url": 1})
                viewers_enriched.append({
                    "user_id": v["user_id"],
                    "full_name": viewer_user.get("full_name", "Ẩn danh") if viewer_user else "Ẩn danh",
                    "avatar_url": viewer_user.get("avatar_url") if viewer_user else None,
                    "viewed_at": v["viewed_at"].isoformat() if isinstance(v.get("viewed_at"), datetime) else v.get("viewed_at"),
                })
            stories.append({
                "id": str(s["_id"]),
                "text_content": s.get("text_content"),
                "media_url": s.get("media_url"),
                "background_color": s.get("background_color", "#18181b"),
                "reactions": s.get("reactions", {}),
                "viewer_count": len(s.get("viewers", [])),
                "viewers": viewers_enriched,
                "created_at": s["created_at"].isoformat() if isinstance(s.get("created_at"), datetime) else s.get("created_at"),
                "expires_at": s["expires_at"].isoformat() if isinstance(s.get("expires_at"), datetime) else s.get("expires_at"),
            })
        return {"stories": stories}

    @staticmethod
    async def record_view(story_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        story = await db["stories"].find_one({"_id": story_id})
        if not story:
            raise HTTPException(status_code=404, detail="Tin không tồn tại hoặc đã hết hạn.")
        existing_viewers = [v["user_id"] for v in story.get("viewers", [])]
        if str(current_user.id) not in existing_viewers:
            await db["stories"].update_one(
                {"_id": story_id},
                {"$push": {"viewers": {"user_id": str(current_user.id), "viewed_at": datetime.now(timezone.utc)}}}
            )
            if story["user_id"] != str(current_user.id):
                await db_client.redis.publish(
                    f"user_notifications:{story['user_id']}",
                    json.dumps({
                        "title": "Có người xem tin của bạn",
                        "body": f"{current_user.full_name} vừa xem tin của bạn.",
                        "link": "/feed"
                    })
                )
logger.info("Log message sanitized"))
        return {"status": "ok"}

    @staticmethod
    async def get_story_viewers(story_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        story = await db["stories"].find_one({"_id": story_id})
        if not story:
            raise HTTPException(status_code=404, detail="Tin không tồn tại.")
        if story["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Bạn không có quyền xem danh sách này.")
        viewers_enriched = []
        for v in story.get("viewers", []):
            viewer_user = await db["users"].find_one({"_id": v["user_id"]}, {"full_name": 1, "avatar_url": 1})
            viewers_enriched.append({
                "user_id": v["user_id"],
                "full_name": viewer_user.get("full_name", "Ẩn danh") if viewer_user else "Ẩn danh",
                "avatar_url": viewer_user.get("avatar_url") if viewer_user else None,
                "viewed_at": v["viewed_at"].isoformat() if isinstance(v.get("viewed_at"), datetime) else v.get("viewed_at"),
            })
        return {"viewers": viewers_enriched, "total": len(viewers_enriched)}

    @staticmethod
    async def react_to_story(story_id: str, reaction_type: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        story = await db["stories"].find_one({"_id": story_id})
        if not story:
            raise HTTPException(status_code=404, detail="Tin không tồn tại.")
        await db["stories"].update_one(
            {"_id": story_id},
            {"$inc": {f"reactions.{reaction_type}": 1}}
        )
logger.info("Log message sanitized"))
        return {"status": "ok", "reaction": reaction_type}

    @staticmethod
    async def vote_story_poll(story_id: str, option_index: int, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        story = await db["stories"].find_one({"_id": story_id})
        if not story:
            raise HTTPException(status_code=404, detail="Tin không tồn tại.")
        poll = story.get("poll_data")
        if not poll:
            raise HTTPException(status_code=400, detail="Tin này không có bình chọn.")
        voters = poll.get("voters", {})
        if str(current_user.id) in voters:
            raise HTTPException(status_code=400, detail="Bạn đã bình chọn rồi.")
        options = poll.get("options", [])
        if option_index < 0 or option_index >= len(options):
            raise HTTPException(status_code=400, detail="Lựa chọn không hợp lệ.")
        await db["stories"].update_one(
            {"_id": story_id},
            {
                "$inc": {f"poll_data.vote_counts.{option_index}": 1},
                "$set": {f"poll_data.voters.{str(current_user.id)}": option_index}
            }
        )
logger.info("Log message sanitized"))
        return {"status": "ok", "voted_index": option_index}

    @staticmethod
    async def answer_story_quiz(story_id: str, option_index: int, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        story = await db["stories"].find_one({"_id": story_id})
        if not story:
            raise HTTPException(status_code=404, detail="Tin không tồn tại.")
        quiz = story.get("quiz_data")
        if not quiz:
            raise HTTPException(status_code=400, detail="Tin này không có câu đố.")
        answers = quiz.get("answers", {})
        if str(current_user.id) in answers:
            raise HTTPException(status_code=400, detail="Bạn đã trả lời rồi.")
        correct_idx = quiz.get("correct_idx", -1)
        is_correct = option_index == correct_idx
        await db["stories"].update_one(
            {"_id": story_id},
            {"$set": {f"quiz_data.answers.{str(current_user.id)}": {"option": option_index, "is_correct": is_correct}}}
        )
logger.info("Log message sanitized"))
        return {"status": "ok", "is_correct": is_correct, "correct_index": correct_idx}

    @staticmethod
    async def reply_to_story(story_id: str, message: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        story = await db["stories"].find_one({"_id": story_id})
        if not story:
            raise HTTPException(status_code=404, detail="Tin không tồn tại.")
        if story["user_id"] == str(current_user.id):
            raise HTTPException(status_code=400, detail="Bạn không thể trả lời tin của chính mình.")
        await db["story_replies"].insert_one({
            "_id": str(uuid.uuid4()),
            "story_id": story_id,
            "sender_id": str(current_user.id),
            "recipient_id": story["user_id"],
            "message": message.strip(),
            "created_at": datetime.now(timezone.utc),
        })
        await db_client.redis.publish(
            f"user_notifications:{story['user_id']}",
            json.dumps({
                "title": "Phản hồi tin mới",
                "body": f"{current_user.full_name}: {message[:60]}",
                "link": "/feed"
            })
        )
logger.info("Log message sanitized"))
        return {"message": "Đã gửi phản hồi."}

    @staticmethod
    async def archive_story(story_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        story = await db["stories"].find_one({"_id": story_id})
        if not story:
            raise HTTPException(status_code=404, detail="Tin không tồn tại.")
        if story["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Bạn không có quyền lưu trữ tin này.")
        await db["stories"].update_one({"_id": story_id}, {"$set": {"is_archived": True}})
logger.info("Log message sanitized"))
        return {"message": "Đã lưu trữ tin."}

    @staticmethod
    async def get_archived_stories(current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        cursor = db["stories"].find(
            {"user_id": str(current_user.id), "is_archived": True}
        ).sort("created_at", -1)
        stories_raw = await cursor.to_list(length=100)
        stories = []
        for s in stories_raw:
            stories.append({
                "id": str(s["_id"]),
                "text_content": s.get("text_content"),
                "media_url": s.get("media_url"),
                "background_color": s.get("background_color", "#18181b"),
                "viewer_count": len(s.get("viewers", [])),
                "reactions": s.get("reactions", {}),
                "created_at": s["created_at"].isoformat() if isinstance(s.get("created_at"), datetime) else s.get("created_at"),
            })
        return {"stories": stories}

    @staticmethod
    async def delete_story(story_id: str, current_user: UserInDB) -> dict:
        db = db_client.mongodb.get_default_database()
        story = await db["stories"].find_one({"_id": story_id})
        if not story:
            raise HTTPException(status_code=404, detail="Tin không tồn tại.")
        if story["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Bạn không có quyền xóa tin này.")
        await db["stories"].delete_one({"_id": story_id})
logger.info("Log message sanitized"))
        return {"message": "Đã xóa tin."}

    @staticmethod
    async def get_story_moderation_queue(skip: int = 0, limit: int = 20) -> list:
        db = db_client.mongodb.get_default_database()
        stories = await db["stories"].find(
            {"moderation_status": "pending"}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        result = []
        for s in stories:
            user = await db["users"].find_one({"_id": s.get("user_id")}, {"full_name": 1})
            result.append({
                "id": str(s["_id"]),
                "user_name": user.get("full_name", "Ẩn danh") if user else "Ẩn danh",
                "content": s.get("text_content", "")[:200],
                "media_url": s.get("media_url"),
                "created_at": s["created_at"].isoformat() if isinstance(s.get("created_at"), datetime) else s.get("created_at"),
            })
        return result

    @staticmethod
    async def moderate_story(story_id: str, action: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        if action not in ["approve", "reject"]:
            raise HTTPException(status_code=400, detail="Hành động không hợp lệ.")
        new_status = "approved" if action == "approve" else "rejected"
        result = await db["stories"].update_one(
            {"_id": story_id},
            {"$set": {"moderation_status": new_status, "moderated_by": str(current_moderator.id), "moderated_at": datetime.now(timezone.utc)}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Story không tồn tại.")
        return {"message": f"Đã {('duyệt' if action == 'approve' else 'từ chối')} Story."}
