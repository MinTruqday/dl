from shared.core.database import db_client
from fastapi import HTTPException
from datetime import datetime
from loguru import logger
class ProfileService:
    @staticmethod
    async def update_profile(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        update_fields = {}
        if "full_name" in data and data["full_name"].strip():
            update_fields["full_name"] = data["full_name"].strip()
        if "bio" in data:
            update_fields["bio"] = data["bio"][:500]
        if "social_links" in data:
            update_fields["social_links"] = data["social_links"]
        if "donation_link" in data:
            update_fields["donation_link"] = data["donation_link"]
        if not update_fields:
            raise HTTPException(status_code=400, detail="Không có thông tin nào để cập nhật.")
        update_fields["updated_at"] = datetime.utcnow()
        await db["users"].update_one(
            {"_id": str(current_user.id)},
            {"$set": update_fields}
        )
logger.info("Log message sanitized"))
        return {"message": "Đã cập nhật hồ sơ cá nhân."}
    @staticmethod
    async def get_user_profile(current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)}, {"password_hash": 0})
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ.")
        user["_id"] = str(user["_id"])
        return user
    @staticmethod
    async def get_badges(current_user):
        db = db_client.mongodb.get_default_database()
        user_record = await db["users"].find_one({"_id": str(current_user.id)})
        badges = user_record.get("badges", []) if user_record else []
        return {"badges": badges}
    @staticmethod
    async def get_reading_streaks(current_user):
        db = db_client.mongodb.get_default_database()
        user_record = await db["users"].find_one({"_id": str(current_user.id)})
        if not user_record:
            return {"current_streak": 0, "longest_streak": 0, "message": "Chưa có thông tin chuỗi đọc."}
        reading_stats = user_record.get("reading_stats", {})
        current_s = reading_stats.get("current_streak", 0)
        longest_s = reading_stats.get("longest_streak", 0)
        return {
            "current_streak": current_s,
            "longest_streak": longest_s,
            "message": f"Tuyệt vời! Bạn đang có chuỗi {current_s} ngày đọc tài liệu." if current_s > 0 else "Hãy bắt đầu đọc tài liệu ngay hôm nay để tích điểm chuỗi!"
        }
    @staticmethod
    async def toggle_bookmark(document_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        user = await db["users"].find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
        bookmarks = user.get("bookmarks", [])
        if document_id in bookmarks:
            await db["users"].update_one({"_id": user_id}, {"$pull": {"bookmarks": document_id}})
            return {"status": "unbookmarked", "message": "Đã xóa khỏi danh sách lưu trữ."}
        await db["users"].update_one({"_id": user_id}, {"$addToSet": {"bookmarks": document_id}})
        return {"status": "bookmarked", "message": "Đã thêm vào danh sách lưu trữ."}
    @staticmethod
    async def get_bookmarks(current_user):
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)})
        bookmark_ids = user.get("bookmarks", []) if user else []
        documents = await db["documents"].find({"_id": {"$in": bookmark_ids}}).to_list(length=100)
        for doc in documents:
            doc["_id"] = str(doc["_id"])
        return documents
    @staticmethod
    async def update_brand_page(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        update_fields = {}
        if "cover_image_url" in data:
            update_fields["author_profile.cover_image_url"] = data["cover_image_url"]
        if "welcome_video_url" in data:
            update_fields["author_profile.welcome_video_url"] = data["welcome_video_url"]
        if "custom_theme" in data:
            update_fields["author_profile.custom_theme"] = data["custom_theme"]
        if not update_fields:
            raise HTTPException(status_code=400, detail="Không có thông tin nào để cập nhật.")
        update_fields["updated_at"] = datetime.utcnow()
        await db["users"].update_one({"_id": str(current_user.id)}, {"$set": update_fields})
logger.info("Log message sanitized"))
        return {"message": "Cập nhật trang tác giả cá nhân thành công."}