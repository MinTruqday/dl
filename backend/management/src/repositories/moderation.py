from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class ModerationRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def insert_moderator_note(cls, *args, **kwargs):
        return await mongo.insert_one("moderator_notes", *args, **kwargs)

    @classmethod
    async def insert_warning(cls, *args, **kwargs):
        return await mongo.insert_one("warnings", *args, **kwargs)

    @classmethod
    async def update_report(cls, *args, **kwargs):
        return await mongo.update_one("reports", *args, **kwargs)

    @classmethod
    async def insert_bug_report(cls, *args, **kwargs):
        return await mongo.insert_one("bug_reports", *args, **kwargs)

    @classmethod
    def find_moderator_activities(cls, *args, **kwargs):
        return mongo.query("moderator_activity").filter(*args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("moderator_notes", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("moderator_notes", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("moderator_notes", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("moderator_notes", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("moderator_notes", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("moderator_notes", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("moderator_notes", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("moderator_notes", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("moderator_notes", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("moderator_notes", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("moderator_notes", *args, **kwargs)
