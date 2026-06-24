from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class ConversationRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await cls._get_db()['conversations'].update_one(*args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await cls._get_db()['conversations'].delete_one(*args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await cls._get_db()['conversations'].find_one(*args, **kwargs)
