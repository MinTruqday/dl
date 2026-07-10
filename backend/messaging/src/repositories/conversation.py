from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class ConversationRepository:
    @staticmethod
    def _get_db():
        db_name = settings.MESSAGING_DB_NAME if hasattr(settings, 'MESSAGING_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("conversations", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("conversations", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("conversations", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("conversations", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("conversations", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("conversations", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("conversations", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("conversations", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("conversations", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("conversations", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("conversations", *args, **kwargs)
