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
        return await cls._get_db()['finetune_jobs'].update_one(*args, **kwargs)

    @classmethod
    async def insert_job(cls, *args, **kwargs):
        return await cls._get_db()['finetune_jobs'].insert_one(*args, **kwargs)

    @classmethod
    async def find_job(cls, *args, **kwargs):
        return await cls._get_db()['finetune_jobs'].find_one(*args, **kwargs)

    @classmethod
    async def update_dataset(cls, *args, **kwargs):
        return await cls._get_db()['finetune_datasets'].update_one(*args, **kwargs)

    @classmethod
    async def delete_dataset(cls, *args, **kwargs):
        return await cls._get_db()['finetune_datasets'].delete_one(*args, **kwargs)

    @classmethod
    async def insert_dataset(cls, *args, **kwargs):
        return await cls._get_db()['finetune_datasets'].insert_one(*args, **kwargs)

    @classmethod
    async def find_dataset(cls, *args, **kwargs):
        return await cls._get_db()['finetune_datasets'].find_one(*args, **kwargs)

    @classmethod
    async def insert_samples(cls, *args, **kwargs):
        return await cls._get_db()['finetune_samples'].insert_many(*args, **kwargs)

    @classmethod
    async def delete_samples(cls, *args, **kwargs):
        return await cls._get_db()['finetune_samples'].delete_many(*args, **kwargs)

    @classmethod
    async def count_samples(cls, *args, **kwargs):
        return await cls._get_db()['finetune_samples'].count_documents(*args, **kwargs)

    @classmethod
    async def delete_sample(cls, *args, **kwargs):
        return await cls._get_db()['finetune_samples'].delete_one(*args, **kwargs)

    @classmethod
    async def find_document_context(cls, *args, **kwargs):
        return await cls._get_db()['documents'].find_one(*args, **kwargs)
