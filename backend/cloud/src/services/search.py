from datetime import datetime, timezone
import re
import uuid
from typing import List, Optional
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
            filter_doc["name"] = {"$regex": re.escape(query_text), "$options": "i"}
        if mime_type:
            filter_doc["mime_type"] = {"$regex": re.escape(mime_type), "$options": "i"}
        if extension:
            if not re.fullmatch(r"[a-zA-Z0-9]{1,10}", extension):
                raise HTTPException(status_code=422, detail="Phần mở rộng tệp không hợp lệ")
            filter_doc["name"] = {"$regex": f"\\.{extension}$", "$options": "i"}
        if min_size_mb is not None and min_size_mb < 0:
            raise HTTPException(status_code=422, detail="Kích thước tối thiểu không hợp lệ")
        if max_size_mb is not None and max_size_mb < 0:
            raise HTTPException(status_code=422, detail="Kích thước tối đa không hợp lệ")
        if (
            min_size_mb is not None
            and max_size_mb is not None
            and min_size_mb > max_size_mb
        ):
            raise HTTPException(
                status_code=422,
                detail="Khoảng kích thước tìm kiếm không hợp lệ",
            )
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
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color_hex):
            raise HTTPException(status_code=422, detail="Mã màu thư mục không hợp lệ")
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
        clean_tags = list(dict.fromkeys(t.strip().lower() for t in tags if t.strip()))
        if len(clean_tags) > 50 or any(len(tag) > 50 for tag in clean_tags):
            raise HTTPException(status_code=422, detail="Danh sách thẻ vượt quá giới hạn")
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
        can_preview = bool(item.get("url")) and preview_type != "generic"
        stream_url = None
        if can_preview:
            from src.core.storage import generate_presigned_url

            stream_url = await generate_presigned_url(item["url"], 900)
        return {
            "item_id": item_id,
            "name": item.get("name"),
            "size": item.get("size"),
            "preview_type": preview_type,
            "stream_url": stream_url,
            "can_preview": can_preview
        }
