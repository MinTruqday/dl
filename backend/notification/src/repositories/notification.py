from src.core.infrastructure.api_client import db_client
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
        return await db_client.update_one("notifications", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await db_client.count_documents("notifications", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await db_client.delete_one("notifications", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await db_client.update_many("notifications", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await db_client.insert_one("notifications", *args, **kwargs)

    @classmethod
    async def update_user_announcement_status(cls, *args, **kwargs):
        return await db_client.update_one("users", *args, **kwargs)
