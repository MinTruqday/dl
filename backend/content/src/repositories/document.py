from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class DocumentRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await cls._get_db()['documents'].update_one(*args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await cls._get_db()['documents'].find_one(*args, **kwargs)

    @classmethod
    async def insert_revision(cls, *args, **kwargs):
        return await cls._get_db()['document_revisions'].insert_one(*args, **kwargs)

    @classmethod
    async def insert_audit_log(cls, *args, **kwargs):
        return await cls._get_db()['audit_logs'].insert_one(*args, **kwargs)

    @classmethod
    async def insert_version(cls, *args, **kwargs):
        return await cls._get_db()['document_versions'].insert_one(*args, **kwargs)
