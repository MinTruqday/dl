from datetime import datetime, timezone

from fastapi import HTTPException, status
from loguru import logger
from src.schemas.notification import Notification, NotificationCreate
from uuid6 import uuid7

from core.config import settings
from core.database import db_client
from core.repositories.base_repository import RepositoryFactory


class NotificationManager:

    @staticmethod
    async def get_notifications(user_id: str, skip: int, limit: int, db):
        cursor = (
            RepositoryFactory.get("notifications")
            .find({"target_user_id": user_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        total = await RepositoryFactory.get("notifications").count_documents(
            {"target_user_id": user_id}
        )
        unread = await RepositoryFactory.get("notifications").count_documents(
            {"target_user_id": user_id, "is_read": False}
        )
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return {"items": docs, "total": total, "unread": unread}

    @staticmethod
    async def mark_as_read(notif_id: str, user_id: str, db):
        result = await RepositoryFactory.get("notifications").update_one(
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
        await RepositoryFactory.get("notifications").update_many(
            {"target_user_id": user_id, "is_read": False}, {"$set": {"is_read": True}}
        )
        return {"success": True}

    @staticmethod
    async def delete_notification(notif_id: str, user_id: str, db):
        result = await RepositoryFactory.get("notifications").delete_one(
            {"_id": notif_id, "target_user_id": user_id}
        )
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lỗi xóa thông báo do không tìm thấy",
            )
        return {"id": notif_id}

    @staticmethod
    async def create_notification(data: NotificationCreate, db):
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
        await RepositoryFactory.get("notifications").insert_one(doc)
        if db_client.redis:
            try:
                import json

                await db_client.redis.publish(
                    f"user_notifications:{data.target_user_id}",
                    json.dumps({"title": data.title, "body": data.body}),
                )
            except Exception:
                logger.error("Lỗi gửi thông báo theo thời gian thực")
        return {"id": notif_id}
