from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class FinetuneRepository:
    @staticmethod
    def _get_db():
        db_name = settings.AGENTIC_AI_DB_NAME if hasattr(settings, 'AGENTIC_AI_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_job(cls, *args, **kwargs):
        return await mongo.update_one("finetune_jobs", *args, **kwargs)

    @classmethod
    async def insert_job(cls, *args, **kwargs):
        return await mongo.insert_one("finetune_jobs", *args, **kwargs)

    @classmethod
    async def find_job(cls, *args, **kwargs):
        return await mongo.find_one("finetune_jobs", *args, **kwargs)

    @classmethod
    async def update_dataset(cls, *args, **kwargs):
        return await mongo.update_one("finetune_datasets", *args, **kwargs)

    @classmethod
    async def delete_dataset(cls, *args, **kwargs):
        return await mongo.delete_one("finetune_datasets", *args, **kwargs)

    @classmethod
    async def insert_dataset(cls, *args, **kwargs):
        return await mongo.insert_one("finetune_datasets", *args, **kwargs)

    @classmethod
    async def find_dataset(cls, *args, **kwargs):
        return await mongo.find_one("finetune_datasets", *args, **kwargs)

    @classmethod
    async def insert_samples(cls, *args, **kwargs):
        return await cls._get_db()['finetune_samples'].insert_many(*args, **kwargs)

    @classmethod
    async def delete_samples(cls, *args, **kwargs):
        return await mongo.delete_many("finetune_samples", *args, **kwargs)

    @classmethod
    async def count_samples(cls, *args, **kwargs):
        return await mongo.count_documents("finetune_samples", *args, **kwargs)

    @classmethod
    async def delete_sample(cls, *args, **kwargs):
        return await mongo.delete_one("finetune_samples", *args, **kwargs)

    @classmethod
    async def find_document_context(cls, *args, **kwargs):
        return await mongo.find_one("documents", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("finetune_jobs", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("finetune_jobs", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("finetune_jobs", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("finetune_jobs", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("finetune_jobs", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("finetune_jobs", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("finetune_jobs", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("finetune_jobs", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("finetune_jobs", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("finetune_jobs", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("finetune_jobs", *args, **kwargs)
