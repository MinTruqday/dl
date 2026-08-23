from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from src.core.dependency import verify_internal_token
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.storage import generate_presigned_url


router = APIRouter(prefix="/noi-bo")


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


@router.post("/luu-tru", dependencies=[Depends(verify_internal_token)], include_in_schema=False)
async def internal_storage_data(req: dict):
    operation = str(req.get("operation", ""))
    query = req.get("query") or {}
    projection = req.get("projection")
    items = database.mongodb[settings.CLOUD_DB_NAME].storage_items
    if operation == "find_one":
        item = await items.find_one(query, projection)
        return {"data": serialize_internal(item)}
    if operation == "find_many":
        limit = min(max(int(req.get("limit") or 100), 1), 200)
        cursor = items.find(query, projection)
        sort = req.get("sort") or []
        if sort:
            cursor = cursor.sort([(str(field), int(direction)) for field, direction in sort])
        rows = await cursor.limit(limit).to_list(length=limit)
        return {"data": serialize_internal(rows)}
    if operation == "preview_url":
        item = await items.find_one(
            {
                "_id": str(req.get("item_id", "")),
                "owner_id": str(req.get("owner_id", "")),
                "is_folder": False,
                "is_trashed": {"$ne": True},
            },
            {"url": 1},
        )
        if not item or not item.get("url"):
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin")
        return {"data": {"preview_url": await generate_presigned_url(item["url"], 900)}}
    raise HTTPException(status_code=422, detail="Thao tác dữ liệu nội bộ không hợp lệ")
