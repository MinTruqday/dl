from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class ChatRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def insert_ai_message(cls, *args, **kwargs):
        return await cls._get_db()['ai_messages'].insert_one(*args, **kwargs)

    @classmethod
    async def find_ai_message(cls, *args, **kwargs):
        return await cls._get_db()['ai_messages'].find_one(*args, **kwargs)

    @classmethod
    async def update_ai_session(cls, *args, **kwargs):
        return await cls._get_db()['ai_sessions'].update_one(*args, **kwargs)

    @classmethod
    async def delete_ai_session(cls, *args, **kwargs):
        return await cls._get_db()['ai_sessions'].delete_one(*args, **kwargs)

    @classmethod
    async def insert_ai_session(cls, *args, **kwargs):
        return await cls._get_db()['ai_sessions'].insert_one(*args, **kwargs)

    @classmethod
    async def find_ai_session(cls, *args, **kwargs):
        return await cls._get_db()['ai_sessions'].find_one(*args, **kwargs)
