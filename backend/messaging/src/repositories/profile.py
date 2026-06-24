from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class ContactProfileRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_contact_profile(cls, *args, **kwargs):
        return await cls._get_db()['user_contact_profiles'].update_one(*args, **kwargs)

    @classmethod
    async def find_contact_profile(cls, *args, **kwargs):
        return await cls._get_db()['user_contact_profiles'].find_one(*args, **kwargs)
