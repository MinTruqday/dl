from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class CollaborationRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def insert_activity(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_activities", *args, **kwargs)

    @classmethod
    async def insert_draft(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_drafts", *args, **kwargs)

    @classmethod
    async def update_invite(cls, *args, **kwargs):
        return await mongo.update_one("collaboration_invites", *args, **kwargs)

    @classmethod
    async def delete_invite(cls, *args, **kwargs):
        return await mongo.delete_one("collaboration_invites", *args, **kwargs)

    @classmethod
    async def insert_invite(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_invites", *args, **kwargs)

    @classmethod
    async def find_invite(cls, *args, **kwargs):
        return await mongo.find_one("collaboration_invites", *args, **kwargs)

    @classmethod
    async def update_invite_code(cls, *args, **kwargs):
        return await mongo.update_one("collaboration_invite_codes", *args, **kwargs)

    @classmethod
    async def find_invite_code(cls, *args, **kwargs):
        return await mongo.find_one("collaboration_invite_codes", *args, **kwargs)

    @classmethod
    async def update_lock(cls, *args, **kwargs):
        return await mongo.update_one("collaboration_locks", *args, **kwargs)

    @classmethod
    async def delete_lock(cls, *args, **kwargs):
        return await mongo.delete_one("collaboration_locks", *args, **kwargs)

    @classmethod
    async def find_lock(cls, *args, **kwargs):
        return await mongo.find_one("collaboration_locks", *args, **kwargs)

    @classmethod
    async def insert_memo(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_memos", *args, **kwargs)

    @classmethod
    async def update_status(cls, *args, **kwargs):
        return await mongo.update_one("collaboration_status", *args, **kwargs)

    @classmethod
    async def update_task(cls, *args, **kwargs):
        return await mongo.update_one("collaboration_tasks", *args, **kwargs)

    @classmethod
    async def insert_task(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_tasks", *args, **kwargs)

    @classmethod
    async def find_task(cls, *args, **kwargs):
        return await mongo.find_one("collaboration_tasks", *args, **kwargs)

    @classmethod
    async def insert_task_comment(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_task_comments", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_activities", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("collaboration_activities", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("collaboration_activities", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("collaboration_activities", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("collaboration_activities", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("collaboration_activities", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("collaboration_activities", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("collaboration_activities", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("collaboration_activities", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("collaboration_activities", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("collaboration_activities", *args, **kwargs)
