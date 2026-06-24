from src.core.infrastructure.mongo_client import mongo_client
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
        return await mongo_client.update_one("documents", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo_client.find_one("documents", *args, **kwargs)

    @classmethod
    async def insert_revision(cls, *args, **kwargs):
        return await mongo_client.insert_one("document_revisions", *args, **kwargs)

    @classmethod
    async def insert_audit_log(cls, *args, **kwargs):
        return await mongo_client.insert_one("audit_logs", *args, **kwargs)

    @classmethod
    async def insert_version(cls, *args, **kwargs):
        return await mongo_client.insert_one("document_versions", *args, **kwargs)
