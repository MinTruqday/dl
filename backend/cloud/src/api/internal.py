from datetime import datetime
import hashlib
import re
from typing import Any
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from src.core.dependency import verify_internal_token
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.storage import download_file, generate_presigned_url, upload_file


router = APIRouter(prefix="/noi-bo")


@router.post("/kiem-thu/nguon-yeu-cau", dependencies=[Depends(verify_internal_token)], include_in_schema=False)
async def store_qa_requirement_source(
    project_id: str = Form(),
    document_id: str = Form(),
    file: UploadFile = File(),
):
    data = await file.read(25 * 1024 * 1024 + 1)
    if not data:
        raise HTTPException(status_code=422, detail={"code": "EMPTY_SOURCE_FILE"})
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"code": "SOURCE_FILE_TOO_LARGE"})
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", file.filename or "requirements.bin").strip("-") or "requirements.bin"
    object_key = f"system/qa/{project_id}/requirements/{document_id}/{safe_name}"
    await upload_file(data, object_key, file.content_type or "application/octet-stream")
    return {"data": {"object_key": object_key, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data), "content_type": file.content_type or "application/octet-stream"}}


@router.get("/kiem-thu/nguon-yeu-cau", dependencies=[Depends(verify_internal_token)], include_in_schema=False)
async def read_qa_requirement_source(
    project_id: str,
    document_id: str,
    object_key: str,
):
    prefix = f"system/qa/{project_id}/requirements/{document_id}/"
    if not object_key.startswith(prefix):
        raise HTTPException(status_code=403, detail={"code": "SOURCE_PATH_FORBIDDEN"})
    data, content_type = await download_file(object_key)
    return Response(content=data, media_type=content_type or "application/octet-stream")


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
