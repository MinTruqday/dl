from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class NotificationRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await cls._get_db()['notifications'].update_one(*args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await cls._get_db()['notifications'].count_documents(*args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await cls._get_db()['notifications'].delete_one(*args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await cls._get_db()['notifications'].update_many(*args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await cls._get_db()['notifications'].insert_one(*args, **kwargs)

    @classmethod
    async def update_user_announcement_status(cls, *args, **kwargs):
        return await cls._get_db()['users'].update_one(*args, **kwargs)
