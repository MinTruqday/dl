from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger

from core.database import db_client


class ProfileService:

    @staticmethod
    async def update_profile(data: dict, current_user, db=None) -> dict:
        if db is None:
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
            raise HTTPException(
                status_code=400, detail="Không thể cập nhật do thiếu thông tin hợp lệ"
            )
        update_fields["updated_at"] = datetime.now(timezone.utc)
        await db["users"].update_one(
            {"_id": str(current_user.id)}, {"$set": update_fields}
        )
        logger.info("Cập nhật hồ sơ cá nhân thành công")
        return {"message": "Cập nhật thông tin cá nhân thành công"}

    @staticmethod
    async def get_user_profile(current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one(
            {"_id": str(current_user.id)}, {"password_hash": 0}
        )
        if not user:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy thông tin hồ sơ"
            )
        user["_id"] = str(user["_id"])
        return user

    @staticmethod
    async def get_badges(current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_record = await db["users"].find_one({"_id": str(current_user.id)})
        badges = user_record.get("badges", []) if user_record else []
        return {"badges": badges}

    @staticmethod
    async def get_reading_streaks(current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_record = await db["users"].find_one({"_id": str(current_user.id)})
        if not user_record:
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "message": "Tài khoản chưa có chuỗi ngày đọc",
            }
        reading_stats = user_record.get("reading_stats", {})
        current_s = reading_stats.get("current_streak", 0)
        longest_s = reading_stats.get("longest_streak", 0)
        return {
            "current_streak": current_s,
            "longest_streak": longest_s,
            "message": (
                "You have successfully maintained an active reading streak for the reported duration"
                if current_s > 0
                else "Begin reading documents to initiate and build your daily activity streak"
            ),
        }

    @staticmethod
    async def update_brand_page(data: dict, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        update_fields = {}
        if "cover_image_url" in data:
            update_fields["author_profile.cover_image_url"] = data["cover_image_url"]
        if "welcome_video_url" in data:
            update_fields["author_profile.welcome_video_url"] = data[
                "welcome_video_url"
            ]
        if "custom_theme" in data:
            update_fields["author_profile.custom_theme"] = data["custom_theme"]
        if not update_fields:
            raise HTTPException(
                status_code=400, detail="Không thể cập nhật do thiếu thông tin hợp lệ"
            )
        update_fields["updated_at"] = datetime.now(timezone.utc)
        await db["users"].update_one(
            {"_id": str(current_user.id)}, {"$set": update_fields}
        )
        logger.info("Cập nhật trang hồ sơ tác giả thành công")
        return {"message": "Cập nhật trang hồ sơ tác giả thành công"}

    @staticmethod
    async def block_user(target_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        if str(current_user.id) == target_id:
            raise HTTPException(status_code=400, detail="Không thể tự chặn chính mình")
        target_user = await db["users"].find_one({"_id": target_id})
        if not target_user:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản đích")
        await db["users"].update_one(
            {"_id": str(current_user.id)}, {"$addToSet": {"blocked_users": target_id}}
        )
        return {"status": "ok", "message": "Đã hạn chế tài khoản tương tác"}
