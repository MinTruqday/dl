from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class CopyrightRepository:
    @staticmethod
    def _get_db():
        db_name = settings.DRM_DB_NAME if hasattr(settings, 'DRM_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_dispute(cls, *args, **kwargs):
        return await mongo.update_one("copyright_disputes", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("copyright_disputes", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("copyright_disputes", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("copyright_disputes", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("copyright_disputes", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("copyright_disputes", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("copyright_disputes", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("copyright_disputes", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("copyright_disputes", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("copyright_disputes", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("copyright_disputes", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("copyright_disputes", *args, **kwargs)
