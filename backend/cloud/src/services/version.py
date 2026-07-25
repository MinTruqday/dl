from datetime import datetime, timezone
from typing import List, Optional
from uuid6 import uuid7
from fastapi import HTTPException
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.logic_logger import log_logic_execution

class VersionService:
    @staticmethod
    @log_logic_execution
    async def create_file_version(file_id: str, owner_id: str, new_url: str, new_size: int) -> dict:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one({"_id": file_id, "owner_id": owner_id})
        if not item or item.get("is_folder"):
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin cần tạo phiên bản")
        version_count = await database.mongodb[settings.CLOUD_DB_NAME].storage_versions.count_documents({"file_id": file_id})
        version_num = version_count + 1
        version_doc = {
            "_id": f"ver_{uuid7()}",
            "file_id": file_id,
            "owner_id": owner_id,
            "version_number": version_num,
            "url": new_url,
            "size": new_size,
            "created_at": datetime.now(timezone.utc),
        }
        await database.mongodb[settings.CLOUD_DB_NAME].storage_versions.insert_one(version_doc)
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_one(
            {"_id": file_id},
            {"$set": {"url": new_url, "size": new_size, "current_version": version_num, "updated_at": datetime.now(timezone.utc)}}
        )
        return {"status": "success", "version": version_num, "file_id": file_id}

    @staticmethod
    @log_logic_execution
    async def get_file_versions(file_id: str, owner_id: str) -> list:
        item = await database.mongodb[settings.CLOUD_DB_NAME].storage_items.find_one({"_id": file_id, "owner_id": owner_id})
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin")
        cursor = database.mongodb[settings.CLOUD_DB_NAME].storage_versions.find({"file_id": file_id}).sort("version_number", -1)
        return await cursor.to_list(length=100)

    @staticmethod
    @log_logic_execution
    async def restore_file_version(file_id: str, version_id: str, owner_id: str) -> dict:
        ver = await database.mongodb[settings.CLOUD_DB_NAME].storage_versions.find_one({"_id": version_id, "file_id": file_id, "owner_id": owner_id})
        if not ver:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên bản tệp tin")
        await database.mongodb[settings.CLOUD_DB_NAME].storage_items.update_one(
            {"_id": file_id},
            {"$set": {"url": ver["url"], "size": ver["size"], "current_version": ver["version_number"], "updated_at": datetime.now(timezone.utc)}}
        )
        return {"status": "success", "message": f"Đã khôi phục về phiên bản {ver['version_number']}"}
