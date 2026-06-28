from src.core.infrastructure.mongo import mongo
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
        return await mongo.update_one("user_contact_profiles", *args, **kwargs)

    @classmethod
    async def find_contact_profile(cls, *args, **kwargs):
        return await mongo.find_one("user_contact_profiles", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("user_contact_profiles", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("user_contact_profiles", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("user_contact_profiles", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("user_contact_profiles", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("user_contact_profiles", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("user_contact_profiles", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("user_contact_profiles", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("user_contact_profiles", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("user_contact_profiles", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("user_contact_profiles", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("user_contact_profiles", *args, **kwargs)
