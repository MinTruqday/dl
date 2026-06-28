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
        await mongo.update_one("users", 
            {"_id": str(current_user.id)}, {"$set": update_fields}
        )
        logger.info("Cập nhật hồ sơ cá nhân thành công")
        return {"message": "Cập nhật thông tin cá nhân thành công"}

    @staticmethod
    async def get_user_profile(current_user) -> dict:
        user = await mongo.find_one("users", 
            {"_id": str(current_user.id)}, {"password_hash": 0}
        )
        if not user:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy thông tin hồ sơ"
            )
        user["_id"] = str(user["_id"])
        return user

    @staticmethod
    async def block_user(target_id: str, current_user) -> dict:
        if str(current_user.id) == target_id:
            raise HTTPException(status_code=400, detail="Không thể tự chặn chính mình")
        target_user = await mongo.find_one(collection="users", query={"_id": target_id})
        if not target_user:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản đích")
        await mongo.update_one("users", 
            {"_id": str(current_user.id)}, {"$addToSet": {"blocked_users": target_id}}
        )
        return {"status": "ok", "message": "Đã hạn chế tài khoản tương tác"}
