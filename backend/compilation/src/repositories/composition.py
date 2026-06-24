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
        return await cls._get_db()['editor_suggestions'].update_one(*args, **kwargs)

    @classmethod
    async def insert_suggestion(cls, *args, **kwargs):
        return await cls._get_db()['editor_suggestions'].insert_one(*args, **kwargs)

    @classmethod
    async def find_suggestion(cls, *args, **kwargs):
        return await cls._get_db()['editor_suggestions'].find_one(*args, **kwargs)

    @classmethod
    async def update_comment(cls, *args, **kwargs):
        return await cls._get_db()['editor_comments'].update_one(*args, **kwargs)

    @classmethod
    async def insert_comment(cls, *args, **kwargs):
        return await cls._get_db()['editor_comments'].insert_one(*args, **kwargs)

    @classmethod
    async def find_comment(cls, *args, **kwargs):
        return await cls._get_db()['editor_comments'].find_one(*args, **kwargs)

    @classmethod
    def find_comments(cls, *args, **kwargs):
        return cls._get_db()['editor_comments'].find(*args, **kwargs)
