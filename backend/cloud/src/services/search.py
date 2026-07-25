from datetime import datetime, timezone
from typing import List, Optional
from uuid6 import uuid7
from fastapi import HTTPException
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.logic_logger import log_logic_execution

class SearchService:
    @staticmethod
    @log_logic_execution
    async def duplicate_item(item_id: str, owner_id: str) -> dict:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one({"_id": item_id, "owner_id": owner_id})
        if not item or item.get("is_folder"):
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin cần nhân bản")
        new_id = f"item_{uuid7()}"
        copy_doc = dict(item)
        copy_doc["_id"] = new_id
        copy_doc["name"] = f"Bản sao của {item.get('name', 'File')}"
        copy_doc["created_at"] = datetime.now(timezone.utc)
        copy_doc["updated_at"] = datetime.now(timezone.utc)
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.insert_one(copy_doc)
        return copy_doc

    @staticmethod
    @log_logic_execution
    async def advanced_search(
        owner_id: str,
        query_text: Optional[str] = None,
        mime_type: Optional[str] = None,
        extension: Optional[str] = None,
        min_size_mb: Optional[float] = None,
        max_size_mb: Optional[float] = None
    ) -> list:
        filter_doc = {"owner_id": owner_id, "is_trashed": False}
        if query_text:
            filter_doc["name"] = {"$regex": query_text, "$options": "i"}
        if mime_type:
            filter_doc["mime_type"] = {"$regex": mime_type, "$options": "i"}
        if extension:
            filter_doc["name"] = {"$regex": f"\\.{extension}$", "$options": "i"}
        size_filter = {}
        if min_size_mb is not None:
            size_filter["$gte"] = int(min_size_mb * 1024 * 1024)
        if max_size_mb is not None:
            size_filter["$lte"] = int(max_size_mb * 1024 * 1024)
        if size_filter:
            filter_doc["size"] = size_filter
        cursor = database.mongodb[settings.CLOUD_DB_NAME].storage_items.find(filter_doc).sort("created_at", -1)
        return await cursor.to_list(length=200)

    @staticmethod
    @log_logic_execution
    async def set_folder_color(folder_id: str, owner_id: str, color_hex: str) -> dict:
        folder = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one({"_id": folder_id, "owner_id": owner_id, "is_folder": True})
        if not folder:
            raise HTTPException(status_code=404, detail="Không tìm thấy thư mục")
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_one(
            {"_id": folder_id},
            {"$set": {"color": color_hex}}
        )
        return {"folder_id": folder_id, "color": color_hex}

    @staticmethod
    @log_logic_execution
    async def update_item_tags(item_id: str, owner_id: str, tags: List[str]) -> dict:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one({"_id": item_id, "owner_id": owner_id})
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin/thư mục")
        clean_tags = list(set([t.strip().lower() for t in tags if t.strip()]))
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_one(
            {"_id": item_id},
            {"$set": {"tags": clean_tags}}
        )
        return {"item_id": item_id, "tags": clean_tags}

    @staticmethod
    @log_logic_execution
    async def get_preview_payload(item_id: str, owner_id: str) -> dict:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one({"_id": item_id, "owner_id": owner_id})
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin")
        mime = item.get("mime_type", "").lower()
        name = item.get("name", "").lower()
        preview_type = "generic"
        if "pdf" in mime or name.endswith(".pdf"):
            preview_type = "pdf"
        elif "image" in mime or name.endswith((".png", ".jpg", ".jpeg", ".webp")):
            preview_type = "image"
        elif "video" in mime or name.endswith((".mp4", ".webm")):
            preview_type = "video"
        elif "text" in mime or name.endswith((".txt", ".py", ".js", ".json", ".md")):
            preview_type = "text"
        return {
            "item_id": item_id,
            "name": item.get("name"),
            "size": item.get("size"),
            "preview_type": preview_type,
            "stream_url": item.get("url"),
            "can_preview": True
        }
