from src.core.infrastructure.mongo_client import mongo_client
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class CompositionRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_suggestion(cls, *args, **kwargs):
        return await mongo_client.update_one("editor_suggestions", *args, **kwargs)

    @classmethod
    async def insert_suggestion(cls, *args, **kwargs):
        return await mongo_client.insert_one("editor_suggestions", *args, **kwargs)

    @classmethod
    async def find_suggestion(cls, *args, **kwargs):
        return await mongo_client.find_one("editor_suggestions", *args, **kwargs)

    @classmethod
    async def update_comment(cls, *args, **kwargs):
        return await mongo_client.update_one("editor_comments", *args, **kwargs)

    @classmethod
    async def insert_comment(cls, *args, **kwargs):
        return await mongo_client.insert_one("editor_comments", *args, **kwargs)

    @classmethod
    async def find_comment(cls, *args, **kwargs):
        return await mongo_client.find_one("editor_comments", *args, **kwargs)

    @classmethod
    def find_comments(cls, *args, **kwargs):
        return mongo_client.query("editor_comments").filter(*args, **kwargs)
