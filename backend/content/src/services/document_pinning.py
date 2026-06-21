import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger

from core.database import db_client
from core.repositories.base_repository import RepositoryFactory


class PinOperations:

    @staticmethod
    async def get_pinned_documents(current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        profile = await RepositoryFactory.get("user_content_profiles").find_one(
            {"_id": str(current_user.id)}, {"pinned_documents": 1}
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
            await RepositoryFactory.get("documents")
            .find({"_id": {"$in": doc_ids}})
            .to_list(length=len(doc_ids))
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
    async def pin_document(document_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await RepositoryFactory.get("user_content_profiles").update_one(
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
        logger.info("Ghim tài liệu thành công")
        return {"status": "success", "message": "Ghim tài liệu ưu tiên thành công"}

    @staticmethod
    async def unpin_document(document_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await RepositoryFactory.get("user_content_profiles").update_one(
            {"_id": str(current_user.id)},
            {"$pull": {"pinned_documents": document_id}},
            upsert=True,
        )
        return {
            "status": "success",
            "message": "Xóa tài liệu khỏi bộ sưu tập ghim thành công",
        }

    @staticmethod
    async def set_pinned_documents(document_ids: list, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await RepositoryFactory.get("user_content_profiles").update_one(
            {"_id": str(current_user.id)},
            {"$set": {"pinned_documents": document_ids}},
            upsert=True,
        )
        return {
            "status": "success",
            "message": "Cập nhật thứ tự tài liệu ghim thành công",
        }
