from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class CompositionRepository:
    @staticmethod
    def _get_db():
        db_name = settings.COMPILATION_DB_NAME if hasattr(settings, 'COMPILATION_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_suggestion(cls, *args, **kwargs):
        return await mongo.update_one("editor_suggestions", *args, **kwargs)

    @classmethod
    async def insert_suggestion(cls, *args, **kwargs):
        return await mongo.insert_one("editor_suggestions", *args, **kwargs)

    @classmethod
    async def find_suggestion(cls, *args, **kwargs):
        return await mongo.find_one("editor_suggestions", *args, **kwargs)

    @classmethod
    async def update_comment(cls, *args, **kwargs):
        return await mongo.update_one("editor_comments", *args, **kwargs)

    @classmethod
    async def insert_comment(cls, *args, **kwargs):
        return await mongo.insert_one("editor_comments", *args, **kwargs)

    @classmethod
    async def find_comment(cls, *args, **kwargs):
        return await mongo.find_one("editor_comments", *args, **kwargs)

    @classmethod
    def find_comments(cls, *args, **kwargs):
        return mongo.query("editor_comments").filter(*args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("editor_suggestions", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("editor_suggestions", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("editor_suggestions", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("editor_suggestions", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("editor_suggestions", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("editor_suggestions", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("editor_suggestions", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("editor_suggestions", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("editor_suggestions", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("editor_suggestions", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("editor_suggestions", *args, **kwargs)
