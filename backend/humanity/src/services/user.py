from typing import Any, Dict, List
from fastapi import HTTPException
from src.repositories.user import UserRepository
from src.schemas.user import CreateUserRequest, Role
from src.core.logic_logger import log_logic_execution
from uuid6 import uuid7
from datetime import datetime, timezone
import re

class UserService:
    @staticmethod
    @log_logic_execution
    async def create_user(req: CreateUserRequest) -> str:
        existing_email = await UserRepository.get_user_by_email(req.email)
        if existing_email:
            raise HTTPException(status_code=400, detail="Địa chỉ email đã được đăng ký trên hệ thống")
        
        existing_slug = await UserRepository.get_user_by_slug(req.slug)
        if existing_slug:
            raise HTTPException(status_code=400, detail="Tên miền cá nhân đã được sử dụng")
            
        user_id = str(uuid7())
        user_doc = req.model_dump()
        user_doc["_id"] = user_id
        user_doc["created_at"] = datetime.now(timezone.utc)
        user_doc["updated_at"] = datetime.now(timezone.utc)
        user_doc["is_active"] = True
        
        await UserRepository.create_user(user_doc)
        return user_id

    @staticmethod
    async def get_all_users(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        users = await UserRepository.get_users_query({}).sort("created_at", -1).skip(offset).limit(limit).execute()
        return [{ "_id": str(u["_id"]), "email": u.get("email"), "full_name": u.get("full_name"), "role": u.get("role"), "is_active": u.get("is_active", True), "created_at": u.get("created_at").isoformat() if hasattr(u.get("created_at"), "isoformat") else u.get("created_at"), "avatar_url": u.get("avatar_url"), "slug": u.get("slug") } for u in users]
        
    @staticmethod
    async def get_user_profile(user_id: str) -> Dict[str, Any]:
        user = await UserRepository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng tương ứng")
        user["_id"] = str(user["_id"])
        return user

    @staticmethod
    async def update_profile(user_id: str, data: dict) -> Dict[str, Any]:
        data["updated_at"] = datetime.now(timezone.utc)
        await UserRepository.update_user(user_id, data)
        return await UserService.get_user_profile(user_id)

    @staticmethod
    async def update_user_role(user_id: str, role: Role) -> dict:
        await UserRepository.update_user(user_id, {"role": role, "updated_at": datetime.now(timezone.utc)})
        return {"status": "success", "role": role}

    @staticmethod
    async def update_user_status(user_id: str, is_active: bool) -> dict:
        await UserRepository.update_user(user_id, {"is_active": is_active, "updated_at": datetime.now(timezone.utc)})
        return {"status": "success", "is_active": is_active}
        
    @staticmethod
    async def search_users(q: str, limit: int = 50) -> List[Dict[str, Any]]:
        query = {}
        if q:
            query = {"$or": [{"email": {"$regex": re.compile(q, re.IGNORECASE)}}, {"full_name": {"$regex": re.compile(q, re.IGNORECASE)}}]}
        users = await UserRepository.get_users_query(query).limit(limit).execute()
        return [{ "_id": str(u["_id"]), "email": u.get("email"), "full_name": u.get("full_name"), "role": u.get("role"), "avatar_url": u.get("avatar_url") } for u in users]
