import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.logic_logger import log_logic_execution

class ShareService:
    @staticmethod
    @log_logic_execution
    async def create_protected_share_link(item_id: str, owner_id: str, password: Optional[str] = None, expires_in_hours: int = 24) -> dict:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one({"_id": item_id, "owner_id": owner_id})
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp cần chia sẻ")
        token = f"share_{secrets.token_urlsafe(16)}"
        pass_hash = hashlib.sha256(password.encode()).hexdigest() if password else None
        share_doc = {
            "_id": token,
            "item_id": item_id,
            "owner_id": owner_id,
            "password_hash": pass_hash,
            "has_password": bool(password),
            "expires_in_hours": expires_in_hours,
            "created_at": datetime.now(timezone.utc),
        }
        await database.mongodb[settings.CLOUD_DB_NAME].storage_share_links.insert_one(share_doc)
        return {"share_token": token, "has_password": bool(password), "expires_in_hours": expires_in_hours}

    @staticmethod
    @log_logic_execution
    async def validate_protected_share_link(token: str, password: Optional[str] = None) -> dict:
        link = await database.mongodb[settings.CLOUD_DB_NAME].storage_share_links.find_one({"_id": token})
        if not link:
            raise HTTPException(status_code=404, detail="Đường dẫn chia sẻ không tồn tại hoặc đã bị hủy")
        if link.get("has_password"):
            if not password:
                raise HTTPException(status_code=401, detail="Yêu cầu nhập mật khẩu bảo vệ để truy cập")
            if hashlib.sha256(password.encode()).hexdigest() != link.get("password_hash"):
                raise HTTPException(status_code=403, detail="Mật khẩu truy cập không chính xác")
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one({"_id": link["item_id"]})
        if not item:
            raise HTTPException(status_code=404, detail="Tệp gốc đã bị xóa")
        return {"item": item, "access_granted": True}
