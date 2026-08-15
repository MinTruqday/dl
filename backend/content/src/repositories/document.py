from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class DocumentRepository:
    @staticmethod
    def _get_db():
        db_name = settings.CONTENT_DB_NAME
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("documents", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("documents", *args, **kwargs)

    @classmethod
    async def insert_revision(cls, *args, **kwargs):
        return await mongo.insert_one("document_revisions", *args, **kwargs)

    @classmethod
    async def insert_version(cls, *args, **kwargs):
        return await mongo.insert_one("document_versions", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("documents", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("documents", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("documents", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("documents", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("documents", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("documents", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("documents", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("documents", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("documents", *args, **kwargs)
