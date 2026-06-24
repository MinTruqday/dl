from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class ReadingRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_history(cls, *args, **kwargs):
        return await cls._get_db()['reading_history'].update_one(*args, **kwargs)

    @classmethod
    async def delete_historys(cls, *args, **kwargs):
        return await cls._get_db()['reading_history'].delete_many(*args, **kwargs)

    @classmethod
    async def delete_history(cls, *args, **kwargs):
        return await cls._get_db()['reading_history'].delete_one(*args, **kwargs)

    @classmethod
    async def update_list(cls, *args, **kwargs):
        return await cls._get_db()['reading_lists'].update_one(*args, **kwargs)

    @classmethod
    async def insert_list(cls, *args, **kwargs):
        return await cls._get_db()['reading_lists'].insert_one(*args, **kwargs)

    @classmethod
    async def find_list(cls, *args, **kwargs):
        return await cls._get_db()['reading_lists'].find_one(*args, **kwargs)
