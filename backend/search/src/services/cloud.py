import re
from typing import Optional
from fastapi import HTTPException
from src.core.logic_logger import log_logic_execution
from src.repositories.cloud import CloudRepository

class CloudService:

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
        cursor = CloudRepository.find(filter_doc).sort("created_at", -1)
        items = await cursor.to_list(length=200)
        for item in items:
            item["_id"] = str(item["_id"])
            if "created_at" in item and hasattr(item["created_at"], "isoformat"):
                item["created_at"] = item["created_at"].isoformat()
            if "updated_at" in item and hasattr(item["updated_at"], "isoformat"):
                item["updated_at"] = item["updated_at"].isoformat()
        return items
