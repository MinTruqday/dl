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
        return await cls._get_db()['system_config'].update_one(*args, **kwargs)

    @classmethod
    async def find_config(cls, *args, **kwargs):
        return await cls._get_db()['system_config'].find_one(*args, **kwargs)

    @classmethod
    async def insert_telemetry(cls, *args, **kwargs):
        return await cls._get_db()['telemetry'].insert_one(*args, **kwargs)

    @classmethod
    async def insert_audit_log(cls, *args, **kwargs):
        return await cls._get_db()['audit_logs'].insert_one(*args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await cls._get_db()['documents'].count_documents(*args, **kwargs)

    @classmethod
    def aggregate_telemetry(cls, *args, **kwargs):
        return cls._get_db()['telemetry'].aggregate(*args, **kwargs)
