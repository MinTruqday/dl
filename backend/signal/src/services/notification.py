from fastapi import HTTPException, status
from core.database import db_client
from core.config import settings
from src.schemas.notification import Notification, NotificationCreate
from uuid6 import uuid7
from datetime import datetime, timezone
from loguru import logger

class NotificationService:

    @staticmethod
    async def get_notifications(user_id: str, skip: int, limit: int, db):
        cursor = db['notifications'].find({'target_user_id': user_id}).sort('created_at', -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        total = await db['notifications'].count_documents({'target_user_id': user_id})
        unread = await db['notifications'].count_documents({'target_user_id': user_id, 'is_read': False})
        for doc in docs:
            doc['_id'] = str(doc['_id'])
        return {'items': docs, 'total': total, 'unread': unread}

    @staticmethod
    async def mark_as_read(notif_id: str, user_id: str, db):
        result = await db['notifications'].update_one(
            {'_id': notif_id, 'target_user_id': user_id},
            {'$set': {'is_read': True}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Thông báo không tồn tại')
        return {'id': notif_id}

    @staticmethod
    async def mark_all_as_read(user_id: str, db):
        await db['notifications'].update_many(
            {'target_user_id': user_id, 'is_read': False},
            {'$set': {'is_read': True}}
        )
        return {'success': True}

    @staticmethod
    async def delete_notification(notif_id: str, user_id: str, db):
        result = await db['notifications'].delete_one({'_id': notif_id, 'target_user_id': user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Thông báo không tồn tại')
        return {'id': notif_id}

    @staticmethod
    async def create_notification(data: NotificationCreate, db):
        notif_id = str(uuid7())
        doc = {
            '_id': notif_id,
            'target_user_id': data.target_user_id,
            'title': data.title,
            'body': data.body,
            'is_read': False,
            'type': data.type,
            'created_at': datetime.now(timezone.utc)
        }
        await db['notifications'].insert_one(doc)
        if db_client.redis:
            try:
                import json
                await db_client.redis.publish(
                    f'user_notifications:{data.target_user_id}',
                    json.dumps({'title': data.title, 'body': data.body})
                )
            except Exception as e:
                logger.error('Lỗi gửi thông báo')
        return {'id': notif_id}
