from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class MessageRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await cls._get_db()['messages'].update_one(*args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await cls._get_db()['messages'].delete_many(*args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await cls._get_db()['messages'].find_one(*args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await cls._get_db()['messages'].update_many(*args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await cls._get_db()['messages'].insert_one(*args, **kwargs)

    @classmethod
    async def update_group(cls, *args, **kwargs):
        return await cls._get_db()['message_groups'].update_one(*args, **kwargs)

    @classmethod
    async def delete_group(cls, *args, **kwargs):
        return await cls._get_db()['message_groups'].delete_one(*args, **kwargs)

    @classmethod
    async def insert_group(cls, *args, **kwargs):
        return await cls._get_db()['message_groups'].insert_one(*args, **kwargs)

    @classmethod
    async def find_group(cls, *args, **kwargs):
        return await cls._get_db()['message_groups'].find_one(*args, **kwargs)

    @classmethod
    async def update_setting(cls, *args, **kwargs):
        return await cls._get_db()['message_settings'].update_one(*args, **kwargs)

    @classmethod
    async def find_setting(cls, *args, **kwargs):
        return await cls._get_db()['message_settings'].find_one(*args, **kwargs)

    @classmethod
    async def find_shared_document(cls, *args, **kwargs):
        return await cls._get_db()['documents'].find_one(*args, **kwargs)
