from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class MessageRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("messages", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("messages", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("messages", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("messages", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("messages", *args, **kwargs)

    @classmethod
    async def update_group(cls, *args, **kwargs):
        return await mongo.update_one("message_groups", *args, **kwargs)

    @classmethod
    async def delete_group(cls, *args, **kwargs):
        return await mongo.delete_one("message_groups", *args, **kwargs)

    @classmethod
    async def insert_group(cls, *args, **kwargs):
        return await mongo.insert_one("message_groups", *args, **kwargs)

    @classmethod
    async def find_group(cls, *args, **kwargs):
        return await mongo.find_one("message_groups", *args, **kwargs)

    @classmethod
    def find_groups(cls, *args, **kwargs):
        return mongo.find("message_groups", *args, **kwargs)

    @classmethod
    async def update_setting(cls, *args, **kwargs):
        return await mongo.update_one("message_settings", *args, **kwargs)

    @classmethod
    async def find_setting(cls, *args, **kwargs):
        return await mongo.find_one("message_settings", *args, **kwargs)

    @classmethod
    async def find_shared_document(cls, *args, **kwargs):
        return await mongo.find_one("documents", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("messages", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("messages", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("messages", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("messages", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("messages", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("messages", *args, **kwargs)
