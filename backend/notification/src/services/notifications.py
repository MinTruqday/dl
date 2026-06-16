import json
from datetime import datetime, timezone
from core.database import db_client
from core.repositories.base import RepositoryFactory
from fastapi import HTTPException, status
from loguru import logger
from src.schemas.notifications import NotificationCreate
from uuid6 import uuid7

class NotificationService:

    @staticmethod
    async def get_notifications(user_id: str, skip: int, limit: int):
        cursor = (
            RepositoryFactory.get("notifications")
            .find({"target_user_id": user_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        total = await RepositoryFactory.get("notifications").count_documents({"target_user_id": user_id})
        unread = await RepositoryFactory.get("notifications").count_documents({"target_user_id": user_id, "is_read": False})
        
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            
        return {"items": docs, "total": total, "unread": unread}

    @staticmethod
    async def mark_as_read(notification_id: str, user_id: str):
        result = await RepositoryFactory.get("notifications").update_one(
            {"_id": notification_id, "target_user_id": user_id},
            {"$set": {"is_read": True}}
        )
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu"
            )
        return {"id": notification_id}

    @staticmethod
    async def mark_all_as_read(user_id: str):
        await RepositoryFactory.get("notifications").update_many(
            {"target_user_id": user_id, "is_read": False},
            {"$set": {"is_read": True}}
        )
        return {"success": True}

    @staticmethod
    async def delete_notification(notification_id: str, user_id: str):
        result = await RepositoryFactory.get("notifications").delete_one(
            {"_id": notification_id, "target_user_id": user_id}
        )
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"
            )
        return {"id": notification_id}

    @staticmethod
    async def create_notification(data: NotificationCreate):
        notification_id = str(uuid7())
        document = {
            "_id": notification_id,
            "target_user_id": data.target_user_id,
            "title": data.title,
            "body": data.body,
            "is_read": False,
            "type": data.type,
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("notifications").insert_one(document)
        
        if db_client.redis:
            try:
                await db_client.redis.publish(
                    f"user_notifications:{data.target_user_id}",
                    json.dumps({"title": data.title, "body": data.body}),
                )
            except Exception:
                logger.error("Mất kết nối mạng tạm thời")
                
        return {"id": notification_id}