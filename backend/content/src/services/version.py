from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
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
    @log_logic_execution
    async def save_version(document_id, version_note, current_user):
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu yêu cầu")
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
        logger.info("Document version snapshot saved")
        return {"message": "Lưu trữ phiên bản lịch sử tài liệu hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def get_versions(document_id, current_user):
        cursor = (
            mongo
            .find("document_versions", {"document_id": document_id, "creator_id": str(current_user.id)})
            .sort("created_at", -1)
        )
        versions = await cursor.to_list(length=None)
        for v in versions:
            v["_id"] = str(v["_id"])
            v["created_at"] = v["created_at"].isoformat()
        return versions

    @staticmethod
    @log_logic_execution
    async def restore_version(version_id: str, current_user):
        version = await mongo.find_one(
            "document_versions", {"_id": version_id, "creator_id": str(current_user.id)}
        )
        if not version:
            raise HTTPException(
                status_code=404, detail="Hệ thống không tìm thấy phiên bản lịch sử yêu cầu"
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
        logger.info("Document version restored")
        return {"message": "Khôi phục tài liệu về phiên bản lịch sử hoàn tất"}
