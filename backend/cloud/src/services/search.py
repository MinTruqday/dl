from datetime import datetime, timezone
import re
import uuid
from typing import List
from fastapi import HTTPException
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database


class SearchService:
    @staticmethod
    async def duplicate_item(item_id: str, owner_id: str) -> dict:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
            {"_id": item_id, "owner_id": owner_id}
        )
        if not item or item.get("is_folder"):
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin cần nhân bản")
        new_id = f"item_{uuid.uuid4()}"
        copy_doc = dict(item)
        copy_doc["_id"] = new_id
        copy_doc["name"] = f"Bản sao của {item.get('name', 'File')}"
        copy_doc["is_public"] = False
        copy_doc["share_token"] = None
        copy_doc["shared_with"] = []
        copy_doc["is_starred"] = False
        copy_doc["created_at"] = datetime.now(timezone.utc)
        copy_doc["updated_at"] = datetime.now(timezone.utc)
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.insert_one(copy_doc)
        return copy_doc

    @staticmethod
    async def set_folder_color(folder_id: str, owner_id: str, color_hex: str) -> dict:
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color_hex):
            raise HTTPException(status_code=422, detail="Mã màu thư mục không hợp lệ")
        folder = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
            {"_id": folder_id, "owner_id": owner_id, "is_folder": True}
        )
        if not folder:
            raise HTTPException(status_code=404, detail="Không tìm thấy thư mục")
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_one(
            {"_id": folder_id}, {"$set": {"color": color_hex}}
        )
        return {"folder_id": folder_id, "color": color_hex}

    @staticmethod
    async def update_item_tags(item_id: str, owner_id: str, tags: List[str]) -> dict:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
            {"_id": item_id, "owner_id": owner_id}
        )
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin/thư mục")
        clean_tags = list(dict.fromkeys(t.strip().lower() for t in tags if t.strip()))
        if len(clean_tags) > 50 or any(len(tag) > 50 for tag in clean_tags):
            raise HTTPException(status_code=422, detail="Danh sách thẻ vượt quá giới hạn")
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_one(
            {"_id": item_id}, {"$set": {"tags": clean_tags}}
        )
        return {"item_id": item_id, "tags": clean_tags}
