from src.core.infrastructure.api_client import db_client
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
        return await db_client.insert_one("moderator_notes", *args, **kwargs)

    @classmethod
    async def insert_warning(cls, *args, **kwargs):
        return await db_client.insert_one("warnings", *args, **kwargs)

    @classmethod
    async def update_report(cls, *args, **kwargs):
        return await db_client.update_one("reports", *args, **kwargs)

    @classmethod
    async def insert_bug_report(cls, *args, **kwargs):
        return await db_client.insert_one("bug_reports", *args, **kwargs)

    @classmethod
    def find_moderator_activities(cls, *args, **kwargs):
        return db_client.query("moderator_activity").filter(*args, **kwargs)
