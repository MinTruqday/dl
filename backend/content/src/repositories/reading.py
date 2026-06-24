from src.core.infrastructure.mongo import mongo
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
        return await mongo.update_one("reading_history", *args, **kwargs)

    @classmethod
    async def delete_historys(cls, *args, **kwargs):
        return await mongo.delete_many("reading_history", *args, **kwargs)

    @classmethod
    async def delete_history(cls, *args, **kwargs):
        return await mongo.delete_one("reading_history", *args, **kwargs)

    @classmethod
    async def update_list(cls, *args, **kwargs):
        return await mongo.update_one("reading_lists", *args, **kwargs)

    @classmethod
    async def insert_list(cls, *args, **kwargs):
        return await mongo.insert_one("reading_lists", *args, **kwargs)

    @classmethod
    async def find_list(cls, *args, **kwargs):
        return await mongo.find_one("reading_lists", *args, **kwargs)
