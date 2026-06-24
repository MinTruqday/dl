from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class ModerationRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def insert_moderator_note(cls, *args, **kwargs):
        return await cls._get_db()['moderator_notes'].insert_one(*args, **kwargs)

    @classmethod
    async def insert_warning(cls, *args, **kwargs):
        return await cls._get_db()['warnings'].insert_one(*args, **kwargs)

    @classmethod
    async def update_report(cls, *args, **kwargs):
        return await cls._get_db()['reports'].update_one(*args, **kwargs)

    @classmethod
    async def insert_bug_report(cls, *args, **kwargs):
        return await cls._get_db()['bug_reports'].insert_one(*args, **kwargs)

    @classmethod
    def find_moderator_activities(cls, *args, **kwargs):
        return cls._get_db()['moderator_activity'].find(*args, **kwargs)
