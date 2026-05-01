from typing import List, Dict, Any
from core.database import db_client
from fastapi import HTTPException
from datetime import datetime
from loguru import logger
from models.user import RoleEnum

class UserService:
    @staticmethod
    async def get_all_users(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        db = db_client.mongodb.get_default_database()
        users = await db["users"].find().sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
        return [
            {
                "id": str(u["_id"]),
                "email": u.get("email"),
                "full_name": u.get("full_name"),
                "role": u.get("role"),
                "is_active": u.get("is_active", True),
                "created_at": u["created_at"].isoformat() if isinstance(u.get("created_at"), datetime) else u.get("created_at"),
            }
            for u in users
        ]

    @staticmethod
    async def update_user_role(user_id: str, role: str) -> Dict[str, str]:
        db = db_client.mongodb.get_default_database()
        res = await db["users"].update_one({"_id": user_id}, {"$set": {"role": role, "updated_at": datetime.utcnow()}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
        logger.info(f"User service: Role for user {user_id} updated to {role}")
        return {"message": f"Đã cập nhật vai trò người dùng thành {role}."}

    @staticmethod
    async def update_user_status(user_id: str, is_active: bool) -> Dict[str, str]:
        db = db_client.mongodb.get_default_database()
        res = await db["users"].update_one({"_id": user_id}, {"$set": {"is_active": is_active, "updated_at": datetime.utcnow()}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
        logger.info(f"User service: User {user_id} status updated to {is_active}")
        return {"message": "Đã cập nhật trạng thái hoạt động của tài khoản."}

    @staticmethod
    async def warn_user(user_id: str, reason: str, moderator_id: str) -> Dict[str, Any]:
        db = db_client.mongodb.get_default_database()
        warn_data = {
            "user_id": user_id,
            "moderator_id": moderator_id,
            "reason": reason,
            "type": "warning",
            "created_at": datetime.utcnow()
        }
        await db["moderation_logs"].insert_one(warn_data)
        logger.info(f"User service: User {user_id} warned by {moderator_id}")
        return {"message": "Đã gửi cảnh báo thành công."}

    @staticmethod
    async def lock_user(user_id: str, reason: str, duration_hours: int, moderator_id: str) -> Dict[str, Any]:
        db = db_client.mongodb.get_default_database()
        lock_data = {
            "user_id": user_id,
            "moderator_id": moderator_id,
            "reason": reason,
            "duration": duration_hours,
            "type": "lock",
            "created_at": datetime.utcnow()
        }
        await db["moderation_logs"].insert_one(lock_data)
        await db["users"].update_one({"_id": user_id}, {"$set": {"is_active": False, "lock_until": datetime.utcnow()}}) # Simplify for now
        logger.info(f"User service: User {user_id} locked by {moderator_id}")
        return {"message": "Khóa tài khoản thành công."}
