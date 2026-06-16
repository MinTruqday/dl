from datetime import datetime, timezone
from core.database import db_client
from fastapi import HTTPException
from loguru import logger

class ProfileService:

    @staticmethod
    async def update_profile(data: dict, current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
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
            raise HTTPException(status_code=400, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
            
        update_fields["updated_at"] = datetime.now(timezone.utc)
        await target_db["users"].update_one({"_id": str(current_user.get("id"))}, {"$set": update_fields})
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {"message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"}

    @staticmethod
    async def get_user_profile(current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        user = await target_db["users"].find_one({"_id": str(current_user.get("id"))}, {"password_hash": 0})
        if not user:
            raise HTTPException(status_code=404, detail="Lỗi truy xuất cơ sở dữ liệu hệ thống")
        user["_id"] = str(user["_id"])
        return user

    @staticmethod
    async def get_badges(current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        user_record = await target_db["users"].find_one({"_id": str(current_user.get("id"))})
        badges = user_record.get("badges", []) if user_record else []
        return {"badges": badges}

    @staticmethod
    async def update_brand_page(data: dict, current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        update_fields = {}
        if "cover_image_url" in data:
            update_fields["author_profile.cover_image_url"] = data["cover_image_url"]
        if "welcome_video_url" in data:
            update_fields["author_profile.welcome_video_url"] = data["welcome_video_url"]
        if "custom_theme" in data:
            update_fields["author_profile.custom_theme"] = data["custom_theme"]
            
        if not update_fields:
            raise HTTPException(status_code=400, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
            
        update_fields["updated_at"] = datetime.now(timezone.utc)
        await target_db["users"].update_one({"_id": str(current_user.get("id"))}, {"$set": update_fields})
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {"message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"}

    @staticmethod
    async def block_user(target_id: str, current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        if str(current_user.get("id")) == target_id:
            raise HTTPException(status_code=400, detail="Lỗi xử lý tài khoản")
            
        target_user = await target_db["users"].find_one({"_id": target_id})
        if not target_user:
            raise HTTPException(status_code=404, detail="Lỗi xử lý tài khoản")
            
        await target_db["users"].update_one({"_id": str(current_user.get("id"))}, {"$addToSet": {"blocked_users": target_id}})
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {"status": "ok", "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"}