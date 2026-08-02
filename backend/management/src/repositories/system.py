from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class SystemRepository:
    @staticmethod
    def _get_db():
        db_name = settings.MANAGEMENT_DB_NAME
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_config(cls, *args, **kwargs):
        return await mongo.update_one("system_config", *args, **kwargs)

    @classmethod
    async def find_config(cls, *args, **kwargs):
        return await mongo.find_one("system_config", *args, **kwargs)

    @classmethod
    async def insert_telemetry(cls, *args, **kwargs):
        return await mongo.insert_one("telemetry", *args, **kwargs)

    @classmethod
    async def insert_audit_log(cls, *args, **kwargs):
        return await mongo.insert_one("audit_logs", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("documents", *args, **kwargs)

    @classmethod
    def aggregate_telemetry(cls, *args, **kwargs):
        return mongo.aggregate("telemetry", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("system_config", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("system_config", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("system_config", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("system_config", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("system_config", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("system_config", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("system_config", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("system_config", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("system_config", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("system_config", *args, **kwargs)
