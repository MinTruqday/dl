from src.core.infrastructure.api_client import db_client
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class SystemRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_config(cls, *args, **kwargs):
        return await db_client.update_one("system_config", *args, **kwargs)

    @classmethod
    async def find_config(cls, *args, **kwargs):
        return await db_client.find_one("system_config", *args, **kwargs)

    @classmethod
    async def insert_telemetry(cls, *args, **kwargs):
        return await db_client.insert_one("telemetry", *args, **kwargs)

    @classmethod
    async def insert_audit_log(cls, *args, **kwargs):
        return await db_client.insert_one("audit_logs", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await db_client.count_documents("documents", *args, **kwargs)

    @classmethod
    def aggregate_telemetry(cls, *args, **kwargs):
        return db_client.aggregate("telemetry", *args, **kwargs)
