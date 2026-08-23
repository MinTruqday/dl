import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database


class ShareService:
    @staticmethod
    async def create_protected_share_link(
        item_id: str, owner_id: str, password: Optional[str] = None, expires_in_hours: int = 24
    ) -> dict:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
            {"_id": item_id, "owner_id": owner_id}
        )
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp cần chia sẻ")
        token = f"share_{secrets.token_urlsafe(16)}"
        password_salt = secrets.token_bytes(16) if password else None
        password_hash = (
            hashlib.scrypt(password.encode(), salt=password_salt, n=16384, r=8, p=1).hex()
            if password and password_salt
            else None
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        share_doc = {
            "_id": token,
            "item_id": item_id,
            "owner_id": owner_id,
            "password_hash": password_hash,
            "password_salt": password_salt.hex() if password_salt else None,
            "has_password": bool(password),
            "expires_in_hours": expires_in_hours,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
        }
        await database.mongodb[settings.CLOUD_DB_NAME].storage_share_links.insert_one(share_doc)
        return {"share_token": token, "has_password": bool(password), "expires_at": expires_at}

    @staticmethod
    async def validate_protected_share_link(token: str, password: Optional[str] = None) -> dict:
        link = await database.mongodb[settings.CLOUD_DB_NAME].storage_share_links.find_one(
            {"_id": token}
        )
        if not link:
            raise HTTPException(
                status_code=404, detail="Đường dẫn chia sẻ không tồn tại hoặc đã bị hủy"
            )
        expires_at = link.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if not isinstance(expires_at, datetime) or expires_at <= datetime.now(timezone.utc):
            await database.mongodb[settings.CLOUD_DB_NAME].storage_share_links.delete_one(
                {"_id": token}
            )
            raise HTTPException(status_code=410, detail="Đường dẫn chia sẻ đã hết hạn")
        if link.get("has_password"):
            if not password:
                raise HTTPException(
                    status_code=401, detail="Yêu cầu nhập mật khẩu bảo vệ để truy cập"
                )
            try:
                candidate = hashlib.scrypt(
                    password.encode(), salt=bytes.fromhex(link["password_salt"]), n=16384, r=8, p=1
                ).hex()
            except (KeyError, TypeError, ValueError):
                raise HTTPException(status_code=410, detail="Đường dẫn chia sẻ không còn hợp lệ")
            if not hmac.compare_digest(candidate, link.get("password_hash", "")):
                raise HTTPException(status_code=403, detail="Mật khẩu truy cập không chính xác")
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
            {"_id": link["item_id"]}
        )
        if not item:
            raise HTTPException(status_code=404, detail="Tệp gốc đã bị xóa")
        if not item.get("is_folder") and item.get("url"):
            from src.services.upload import UploadService

            item.update(await UploadService.get_presigned_url(item["url"]))
        return {"item": item, "access_granted": True}
