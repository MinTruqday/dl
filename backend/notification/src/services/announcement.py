from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.redis import redis
from datetime import datetime, timezone

from fastapi import HTTPException, status
from loguru import logger
from pymongo.errors import DuplicateKeyError
from src.schemas.announcement import AnnouncementCreate
from src.repositories.announcement import AnnouncementRepository
from src.services.humanity_client import HumanityClient

class AnnouncementService:

    @staticmethod
    @log_logic_execution
    async def get_announcements(user_id: str, skip: int, limit: int, db):
        cursor = (
            AnnouncementRepository
            .find({"target_user_id": user_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        total = await AnnouncementRepository.count_documents(
            {"target_user_id": user_id}
        )
        unread = await AnnouncementRepository.count_documents(
            {"target_user_id": user_id, "is_read": False}
        )
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return {"items": docs, "total": total, "unread": unread}

    @staticmethod
    @log_logic_execution
    async def mark_as_read(notif_id: str, user_id: str, db):
        result = await AnnouncementRepository.update_one(
            {"_id": notif_id, "target_user_id": user_id}, {"$set": {"is_read": True}}
        )
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy thông báo hoặc không có quyền truy cập",
            )
        return {"id": notif_id}

    @staticmethod
    @log_logic_execution
    async def mark_all_as_read(user_id: str, db):
        await AnnouncementRepository.update_many(
            {"target_user_id": user_id, "is_read": False}, {"$set": {"is_read": True}}
        )
        return {"success": True}

    @staticmethod
    @log_logic_execution
    async def delete_announcement(notif_id: str, user_id: str, db):
        result = await AnnouncementRepository.delete_one(
            {"_id": notif_id, "target_user_id": user_id}
        )
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lỗi xóa thông báo do không tìm thấy",
            )
        return {"id": notif_id}

    @staticmethod
    @log_logic_execution
    async def create_announcement(data: AnnouncementCreate, db):
        if data.idempotency_key:
            existing = await AnnouncementRepository.find_one(
                {"idempotency_key": data.idempotency_key}
            )
            if existing:
                return {"id": str(existing["_id"]), "duplicate": True}
        profile = await HumanityClient.get(data.target_user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Không tìm thấy người nhận thông báo")
        notif_id = str(uuid.uuid4())
        doc = {
            "_id": notif_id,
            "target_user_id": data.target_user_id,
            "title": data.title,
            "body": data.body,
            "is_read": False,
            "type": data.type,
            "idempotency_key": data.idempotency_key,
            "created_at": datetime.now(timezone.utc),
        }
        try:
            await AnnouncementRepository.insert_one(doc)
        except DuplicateKeyError:
            existing = await AnnouncementRepository.find_one(
                {"idempotency_key": data.idempotency_key}
            )
            return {"id": str(existing["_id"]), "duplicate": True}
        try:
            import json
            await redis.publish(
                f"user_announcements:{data.target_user_id}",
                json.dumps({"title": data.title, "body": data.body}),
            )
        except Exception:
            logger.exception("Failed to distribute real-time notification")
        return {"id": notif_id}
import uuid
