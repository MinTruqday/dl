from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger

from src.core.infrastructure.database import database

class PinService:

    @staticmethod
    @log_logic_execution
    async def get_pinned_documents(current_user) -> list:
        profile = await mongo.find_one(
            "user_content_profiles", {"_id": str(current_user.id)}, projection={"pinned_documents": 1}
        )
        if not profile or "pinned_documents" not in profile:
            return []
        pinned_data = profile["pinned_documents"]
        doc_ids = []
        pinned_at_map = {}
        for item in pinned_data:
            if isinstance(item, str):
                doc_ids.append(item)
                pinned_at_map[item] = None
            else:
                d_id = item.get("document_id")
                doc_ids.append(d_id)
                pinned_at_map[d_id] = item.get("pinned_at")
        docs = (
            await mongo
            .find("documents", {"_id": {"$in": doc_ids}})
            .to_list(length=None)
        )
        doc_map = {str(d["_id"]): d for d in docs}
        result = []
        for d_id in doc_ids:
            if d_id in doc_map:
                d = doc_map[d_id]
                result.append(
                    {
                        "_id": str(d["_id"]),
                        "title": d.get("title", ""),
                        "slug": d.get("slug", ""),
                        "cover_url": d.get("cover_url"),
                        "creator_id": d.get("creator_id"),
                        "pinned_at": pinned_at_map.get(d_id),
                    }
                )
        return result

    @staticmethod
    @log_logic_execution
    async def pin_document(document_id: str, current_user) -> dict:
        await mongo.update_one(
            "user_content_profiles",
            {"_id": str(current_user.id)},
            {
                "$addToSet": {
                    "pinned_documents": {
                        "document_id": document_id,
                        "pinned_at": datetime.now(timezone.utc),
                    }
                }
            },
            upsert=True,
        )
        logger.info("Document pinned to user collection")
        return {"status": "success", "message": "Ghim tài liệu vào danh sách ưu tiên hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def unpin_document(document_id: str, current_user) -> dict:
        await mongo.update_one(
            "user_content_profiles",
            {"_id": str(current_user.id)},
            {"$pull": {"pinned_documents": document_id}},
            upsert=True,
        )
        return {
            "status": "success",
            "message": "Hủy ghim tài liệu khỏi danh sách ưu tiên hoàn tất",
        }

    @staticmethod
    @log_logic_execution
    async def set_pinned_documents(document_ids: list, current_user) -> dict:
        await mongo.update_one(
            "user_content_profiles",
            {"_id": str(current_user.id)},
            {"$set": {"pinned_documents": document_ids}},
            upsert=True,
        )
        return {
            "status": "success",
            "message": "Cập nhật danh sách tài liệu ghim hoàn tất",
        }
