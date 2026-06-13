import json
import re
import uuid
from datetime import datetime, timezone

from bson import ObjectId
from core.database import db_client
from core.repositories.base_repository import RepositoryFactory
from fastapi import HTTPException
from loguru import logger


class VersionsService:

    @staticmethod
    async def save_version(document_id, version_note, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": document_id, "author_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")
        await RepositoryFactory.get("document_versions").insert_one(
            {
                "document_id": document_id,
                "author_id": str(current_user.id),
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
        logger.info(f"Người dùng {current_user.id} lưu bản nháp tài liệu {document_id}")
        return {"message": "Đã lưu bản nháp tài liệu"}

    @staticmethod
    async def get_versions(document_id, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        cursor = (
            RepositoryFactory.get("document_versions")
            .find({"document_id": document_id, "author_id": str(current_user.id)})
            .sort("created_at", -1)
        )
        versions = await cursor.to_list(length=100)
        for v in versions:
            v["_id"] = str(v["_id"])
            v["created_at"] = v["created_at"].isoformat()
        return versions

    @staticmethod
    async def restore_version(version_id: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        version = await RepositoryFactory.get("document_versions").find_one(
            {"_id": ObjectId(version_id), "author_id": str(current_user.id)}
        )
        if not version:
            raise HTTPException(status_code=404, detail="Phiên bản không tồn tại")
        snapshot = version.get("snapshot")
        if not snapshot:
            update_data = {
                "content": version.get("content", ""),
                "updated_at": datetime.now(timezone.utc),
            }
        else:
            update_data = {**snapshot, "updated_at": datetime.now(timezone.utc)}
        await RepositoryFactory.get("documents").update_one(
            {"_id": version["document_id"]}, {"$set": update_data}
        )
        logger.info(
            f"Người dùng {current_user.id} khôi phục tài liệu {version['document_id']} về phiên bản {version_id}"
        )
        return {"message": "Đã khôi phục phiên bản tài liệu"}
