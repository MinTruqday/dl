from typing import Any, Dict, List
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from src.repositories.user import UserRepository
from src.schemas.user import CreateUserRequest, Role
from src.core.logic_logger import log_logic_execution
from uuid6 import uuid7
from datetime import datetime, timedelta, timezone
import re

class UserService:
    PUBLIC_FIELDS = (
        "_id",
        "full_name",
        "slug",
        "role",
        "bio",
        "avatar_url",
        "cover_url",
        "location",
        "website",
        "is_verified",
        "creator_status",
    )

    @staticmethod
    def to_public_user(user: dict) -> dict:
        result = {key: user.get(key) for key in UserService.PUBLIC_FIELDS if key in user}
        if "_id" in result:
            result["_id"] = str(result["_id"])
        return result

    @staticmethod
    @log_logic_execution
    async def create_user(req: CreateUserRequest) -> str:
        email = req.email.lower()
        slug = req.slug.lower()
        existing_email = await UserRepository.get_user_by_email(email)
        if existing_email:
            raise HTTPException(status_code=400, detail="Địa chỉ email đã được đăng ký trên hệ thống")
        
        existing_slug = await UserRepository.get_user_by_slug(slug)
        if existing_slug:
            raise HTTPException(status_code=400, detail="Tên miền cá nhân đã được sử dụng")
            
        user_id = str(uuid7())
        user_doc = req.model_dump()
        user_doc["email"] = email
        user_doc["slug"] = slug
        user_doc["_id"] = user_id
        user_doc["created_at"] = datetime.now(timezone.utc)
        user_doc["updated_at"] = datetime.now(timezone.utc)
        user_doc["is_active"] = True
        
        try:
            await UserRepository.create_user(user_doc)
        except DuplicateKeyError:
            raise HTTPException(status_code=409, detail="Email hoặc tên miền cá nhân đã được sử dụng")
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
        user = await UserRepository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng tương ứng")
        await UserRepository.update_user(user_id, {"role": role.value, "updated_at": datetime.now(timezone.utc)})
        return {"status": "success", "role": role}

    @staticmethod
    async def update_user_status(user_id: str, is_active: bool) -> dict:
        user = await UserRepository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng tương ứng")
        await UserRepository.update_user(user_id, {"is_active": is_active, "updated_at": datetime.now(timezone.utc)})
        if not is_active:
            from src.core.infrastructure.redis import redis
            await redis.delete(f"user_sessions:{user_id}")
        return {"status": "success", "is_active": is_active}
        
    @staticmethod
    async def search_users(q: str, limit: int = 50) -> List[Dict[str, Any]]:
        query = {}
        if q:
            escaped = re.escape(q.strip()[:100])
            query = {"$or": [{"slug": {"$regex": escaped, "$options": "i"}}, {"full_name": {"$regex": escaped, "$options": "i"}}]}
        users = await UserRepository.get_users_query(query).limit(limit).execute()
        return [UserService.to_public_user(user) for user in users]

    @staticmethod
    async def delete_internal_user(user_id: str) -> dict:
        user = await UserRepository.get_user_by_id(user_id)
        if not user:
            return {"deleted": False}
        created_at = user.get("created_at")
        if isinstance(created_at, datetime) and created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if not isinstance(created_at, datetime) or created_at < datetime.now(timezone.utc) - timedelta(minutes=5):
            raise HTTPException(status_code=409, detail="Chỉ có thể thu hồi hồ sơ vừa được khởi tạo")
        result = await UserRepository.delete_user(user_id)
        return {"deleted": result.deleted_count == 1}

    @staticmethod
    async def update_internal_user(user_id: str, data: dict) -> dict:
        allowed_fields = {
            "bookmarks",
            "pinned_documents",
            "wallet_balance",
            "storage_limit",
            "is_premium",
            "creator_status",
            "kyc_status",
            "is_verified",
            "settings",
            "updated_at",
            "blocked_users",
        }
        allowed_operators = {"$set", "$addToSet", "$pull"}
        if not isinstance(data, dict) or not data:
            raise HTTPException(status_code=400, detail="Dữ liệu cập nhật không hợp lệ")
        if any(key.startswith("$") for key in data):
            if any(key not in allowed_operators for key in data):
                raise HTTPException(status_code=400, detail="Toán tử cập nhật không được hỗ trợ")
            for values in data.values():
                if not isinstance(values, dict) or any(field not in allowed_fields for field in values):
                    raise HTTPException(status_code=400, detail="Trường cập nhật không được hỗ trợ")
        elif any(field not in allowed_fields for field in data):
            raise HTTPException(status_code=400, detail="Trường cập nhật không được hỗ trợ")
        result = await UserRepository.update_user(user_id, data)
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng tương ứng")
        return {"updated": result.modified_count == 1}
