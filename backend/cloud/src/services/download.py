from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.storage import get_bucket, get_storage_client

class DownloadService:
    @staticmethod
    async def generate_download_url(file_id: str, owner_id: str, expires_in: int = 3600) -> dict:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one(
            {"_id": file_id, "owner_id": owner_id, "is_folder": False}
        )
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin")

        url = item.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="Tệp tin không có dữ liệu lưu trữ đối tượng")

        client = await get_storage_client()
        bucket = get_bucket(url)
        presigned_url = await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": url},
            ExpiresIn=expires_in,
        )
        return {
            "file_id": file_id,
            "download_url": presigned_url,
            "expires_in": expires_in,
            "name": item.get("name"),
            "size": item.get("size"),
            "mime_type": item.get("mime_type"),
        }
