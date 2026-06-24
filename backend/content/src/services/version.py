from src.core.infrastructure.mongo_client import mongo_client
import json
import re
import uuid
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException
from loguru import logger

from src.core.infrastructure.database import database
from src.repositories.document import DocumentRepository
from src.repositories.document import DocumentRepository


class VersionService:

    @staticmethod
    async def save_version(document_id, version_note, current_user):
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn")
        await DocumentRepository.insert_version(
            {
                "document_id": document_id,
                "creator_id": str(current_user.id),
                "note": version_note,
                "snapshot": {
                    "title": doc.get("title"),
                    "description": doc.get("description"),
                    "content": doc.get("content", ""),
                    "cover_url": doc.get("cover_url"),
                    "tags": doc.get("tags", []),
                    "categories": doc.get("categories", []),
                },
                "created_at": datetime.now(timezone.utc),
            }
        )
        logger.info("Lưu bản chụp lịch sử tài liệu thành công")
        return {"message": "Lưu bản nháp lịch sử thành công"}

    @staticmethod
    async def get_versions(document_id, current_user):
        cursor = (
            DocumentVersionRepository
            .find({"document_id": document_id, "creator_id": str(current_user.id)})
            .sort("created_at", -1)
        )
        versions = await cursor # NO LONGER NEED TO_LIST: result is already list. Remove `await cursor.execute()` manually.
        for v in versions:
            v["_id"] = str(v["_id"])
            v["created_at"] = v["created_at"].isoformat()
        return versions

    @staticmethod
    async def restore_version(version_id: str, current_user):
        version = await db["document_versions"].find_one(
            {"_id": version_id, "creator_id": str(current_user.id)}
        )
        if not version:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy bản chụp lịch sử"
            )
        snapshot = version.get("snapshot")
        if not snapshot:
            update_data = {
                "content": version.get("content", ""),
                "updated_at": datetime.now(timezone.utc),
            }
        else:
            update_data = {**snapshot, "updated_at": datetime.now(timezone.utc)}
        await DocumentRepository.update_one(
            {"_id": version["document_id"]}, {"$set": update_data}
        )
        logger.info("Khôi phục phiên bản lịch sử tài liệu thành công")
        return {"message": "Khôi phục phiên bản lịch sử thành công"}
