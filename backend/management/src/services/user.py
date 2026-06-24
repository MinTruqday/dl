from src.core.infrastructure.mongo import mongo
from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger

from src.core.infrastructure.database import database


class UserService:

    @staticmethod
    async def update_profile(data: dict, current_user) -> dict:
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
    async def get_user_profile(current_user) -> dict:
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
    async def update_brand_page(data: dict, current_user) -> dict:
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
    async def block_user(target_id: str, current_user) -> dict:
        if str(current_user.id) == target_id:
            raise HTTPException(status_code=400, detail="Không thể tự chặn chính mình")
        target_user = await mongo.find_one(collection="users", query={"_id": target_id})
        if not target_user:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản đích")
        await db["users"].update_one(
            {"_id": str(current_user.id)}, {"$addToSet": {"blocked_users": target_id}}
        )
        return {"status": "ok", "message": "Đã hạn chế tài khoản tương tác"}
