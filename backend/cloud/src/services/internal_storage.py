from datetime import datetime
from typing import Any

from fastapi import HTTPException

from src.core.storage import generate_presigned_url
from src.repositories import storage_repository


def serialize_internal(value: Any):
    if isinstance(value, dict):
        return {key: serialize_internal(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize_internal(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


class InternalStorageService:
    @staticmethod
    async def execute(request: dict):
        operation = str(request.get("operation", ""))
        query = request.get("query") or {}
        projection = request.get("projection")
        if operation == "find_one":
            return serialize_internal(await storage_repository.find_one(query, projection))
        if operation == "find_many":
            limit = min(max(int(request.get("limit") or 100), 1), 200)
            sort = request.get("sort") or []
            normalized_sort = [
                (str(field), int(direction)) for field, direction in sort
            ]
            return serialize_internal(
                await storage_repository.find_many(
                    query,
                    projection,
                    sort=normalized_sort,
                    limit=limit,
                )
            )
        if operation == "preview_url":
            item = await storage_repository.find_one(
                {
                    "_id": str(request.get("item_id", "")),
                    "owner_id": str(request.get("owner_id", "")),
                    "is_folder": False,
                    "is_trashed": {"$ne": True},
                },
                {"url": 1},
            )
            if not item or not item.get("url"):
                raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin")
            return {"preview_url": await generate_presigned_url(item["url"], 900)}
        raise HTTPException(status_code=422, detail="Thao tác dữ liệu nội bộ không hợp lệ")
