from src.core.api_client import db_client
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class FinetuneRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_job(cls, *args, **kwargs):
        return await db_client.update_one("finetune_jobs", *args, **kwargs)

    @classmethod
    async def insert_job(cls, *args, **kwargs):
        return await db_client.insert_one("finetune_jobs", *args, **kwargs)

    @classmethod
    async def find_job(cls, *args, **kwargs):
        return await db_client.find_one("finetune_jobs", *args, **kwargs)

    @classmethod
    async def update_dataset(cls, *args, **kwargs):
        return await db_client.update_one("finetune_datasets", *args, **kwargs)

    @classmethod
    async def delete_dataset(cls, *args, **kwargs):
        return await db_client.delete_one("finetune_datasets", *args, **kwargs)

    @classmethod
    async def insert_dataset(cls, *args, **kwargs):
        return await db_client.insert_one("finetune_datasets", *args, **kwargs)

    @classmethod
    async def find_dataset(cls, *args, **kwargs):
        return await db_client.find_one("finetune_datasets", *args, **kwargs)

    @classmethod
    async def insert_samples(cls, *args, **kwargs):
        return await cls._get_db()['finetune_samples'].insert_many(*args, **kwargs)

    @classmethod
    async def delete_samples(cls, *args, **kwargs):
        return await db_client.delete_many("finetune_samples", *args, **kwargs)

    @classmethod
    async def count_samples(cls, *args, **kwargs):
        return await db_client.count_documents("finetune_samples", *args, **kwargs)

    @classmethod
    async def delete_sample(cls, *args, **kwargs):
        return await db_client.delete_one("finetune_samples", *args, **kwargs)

    @classmethod
    async def find_document_context(cls, *args, **kwargs):
        return await db_client.find_one("documents", *args, **kwargs)
