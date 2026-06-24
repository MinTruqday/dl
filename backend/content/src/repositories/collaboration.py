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
        return await cls._get_db()['collaboration_activities'].insert_one(*args, **kwargs)

    @classmethod
    async def insert_draft(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_drafts'].insert_one(*args, **kwargs)

    @classmethod
    async def update_invite(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_invites'].update_one(*args, **kwargs)

    @classmethod
    async def delete_invite(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_invites'].delete_one(*args, **kwargs)

    @classmethod
    async def insert_invite(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_invites'].insert_one(*args, **kwargs)

    @classmethod
    async def find_invite(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_invites'].find_one(*args, **kwargs)

    @classmethod
    async def update_invite_code(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_invite_codes'].update_one(*args, **kwargs)

    @classmethod
    async def find_invite_code(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_invite_codes'].find_one(*args, **kwargs)

    @classmethod
    async def update_lock(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_locks'].update_one(*args, **kwargs)

    @classmethod
    async def delete_lock(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_locks'].delete_one(*args, **kwargs)

    @classmethod
    async def find_lock(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_locks'].find_one(*args, **kwargs)

    @classmethod
    async def insert_memo(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_memos'].insert_one(*args, **kwargs)

    @classmethod
    async def update_status(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_status'].update_one(*args, **kwargs)

    @classmethod
    async def update_task(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_tasks'].update_one(*args, **kwargs)

    @classmethod
    async def insert_task(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_tasks'].insert_one(*args, **kwargs)

    @classmethod
    async def find_task(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_tasks'].find_one(*args, **kwargs)

    @classmethod
    async def insert_task_comment(cls, *args, **kwargs):
        return await cls._get_db()['collaboration_task_comments'].insert_one(*args, **kwargs)
