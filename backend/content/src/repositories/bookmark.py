from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class BookmarkRepository:
    @staticmethod
    def _get_db():
        db_name = settings.CONTENT_DB_NAME if hasattr(settings, 'CONTENT_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_folder(cls, *args, **kwargs):
        return await mongo.update_one("bookmark_folders", *args, **kwargs)

    @classmethod
    async def delete_folder(cls, *args, **kwargs):
        return await mongo.delete_one("bookmark_folders", *args, **kwargs)

    @classmethod
    async def insert_folder(cls, *args, **kwargs):
        return await mongo.insert_one("bookmark_folders", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("bookmark_folders", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("bookmark_folders", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("bookmark_folders", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("bookmark_folders", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("bookmark_folders", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("bookmark_folders", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("bookmark_folders", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("bookmark_folders", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("bookmark_folders", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("bookmark_folders", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("bookmark_folders", *args, **kwargs)
