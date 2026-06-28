from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class ChatRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def insert_ai_message(cls, *args, **kwargs):
        return await mongo.insert_one("ai_messages", *args, **kwargs)

    @classmethod
    async def find_ai_message(cls, *args, **kwargs):
        return await mongo.find_one("ai_messages", *args, **kwargs)

    @classmethod
    async def update_ai_session(cls, *args, **kwargs):
        return await mongo.update_one("ai_sessions", *args, **kwargs)

    @classmethod
    async def delete_ai_session(cls, *args, **kwargs):
        return await mongo.delete_one("ai_sessions", *args, **kwargs)

    @classmethod
    async def insert_ai_session(cls, *args, **kwargs):
        return await mongo.insert_one("ai_sessions", *args, **kwargs)

    @classmethod
    async def find_ai_session(cls, *args, **kwargs):
        return await mongo.find_one("ai_sessions", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("ai_messages", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("ai_messages", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("ai_messages", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("ai_messages", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("ai_messages", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("ai_messages", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("ai_messages", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("ai_messages", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("ai_messages", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("ai_messages", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("ai_messages", *args, **kwargs)
