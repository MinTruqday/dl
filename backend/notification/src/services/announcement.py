from src.core.infrastructure.redis_client import redis_client
from src.core.infrastructure.mongo import mongo
from datetime import datetime, timezone

from fastapi import HTTPException, status
from loguru import logger
from src.schemas.announcement import Announcement, AnnouncementCreate
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.repositories.notification import NotificationRepository


class AnnouncementService:

    @staticmethod
    async def get_notifications(user_id: str, skip: int, limit: int, db):
        cursor = (
            NotificationRepository
            .find({"target_user_id": user_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor # NO LONGER NEED TO_LIST: result is already list. Remove `await cursor.execute()` manually.
        total = await NotificationRepository.count_documents(
            {"target_user_id": user_id}
        )
        unread = await NotificationRepository.count_documents(
            {"target_user_id": user_id, "is_read": False}
        )
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return {"items": docs, "total": total, "unread": unread}

    @staticmethod
    async def mark_as_read(notif_id: str, user_id: str, db):
        result = await NotificationRepository.update_one(
            {"_id": notif_id, "target_user_id": user_id}, {"$set": {"is_read": True}}
        )
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy thông báo hoặc không có quyền truy cập",
            )
        return {"id": notif_id}

    @staticmethod
    async def mark_all_as_read(user_id: str, db):
        await NotificationRepository.update_many(
            {"target_user_id": user_id, "is_read": False}, {"$set": {"is_read": True}}
        )
        return {"success": True}

    @staticmethod
    async def delete_notification(notif_id: str, user_id: str, db):
        result = await NotificationRepository.delete_one(
            {"_id": notif_id, "target_user_id": user_id}
        )
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lỗi xóa thông báo do không tìm thấy",
            )
        return {"id": notif_id}

    @staticmethod
    async def create_notification(data: AnnouncementCreate, db):
        notif_id = str(uuid7())
        doc = {
            "_id": notif_id,
            "target_user_id": data.target_user_id,
            "title": data.title,
            "body": data.body,
            "is_read": False,
            "type": data.type,
            "created_at": datetime.now(timezone.utc),
        }
        await NotificationRepository.insert_one(doc)
        try:
            import json
            await redis_client.publish(
                f"user_notifications:{data.target_user_id}",
                json.dumps({"title": data.title, "body": data.body}),
            )
        except Exception as e:
                logger.error(f"Lỗi gửi thông báo theo thời gian thực: {e}")
        return {"id": notif_id}
