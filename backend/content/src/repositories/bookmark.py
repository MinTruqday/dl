from src.core.infrastructure.api_client import db_client
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class BookmarkRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_folder(cls, *args, **kwargs):
        return await db_client.update_one("bookmark_folders", *args, **kwargs)

    @classmethod
    async def delete_folder(cls, *args, **kwargs):
        return await db_client.delete_one("bookmark_folders", *args, **kwargs)

    @classmethod
    async def insert_folder(cls, *args, **kwargs):
        return await db_client.insert_one("bookmark_folders", *args, **kwargs)
