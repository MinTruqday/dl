from typing import Any, Dict, List, Optional

from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings


class DatabaseRepository:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    @property
    def collection(self):
        db = database.mongodb.get_database(settings.SERVICE_DB_NAME)
        return db[self.collection_name]

    async def find_one(self, query: Dict[str, Any], **kwargs):
        return await self.collection.find_one(query, **kwargs)

    def find(self, *args, **kwargs):
        return self.collection.find(*args, **kwargs)

    async def insert_one(self, document: Dict[str, Any], **kwargs):
        return await self.collection.insert_one(document, **kwargs)

    async def insert_many(self, documents: List[Dict[str, Any]], **kwargs):
        return await self.collection.insert_many(documents, **kwargs)

    async def update_one(
        self, filter: Dict[str, Any], update: Dict[str, Any], **kwargs
    ):
        return await self.collection.update_one(filter, update, **kwargs)

    async def update_many(
        self, filter: Dict[str, Any], update: Dict[str, Any], **kwargs
    ):
        return await self.collection.update_many(filter, update, **kwargs)

    async def delete_one(self, filter: Dict[str, Any], **kwargs):
        return await self.collection.delete_one(filter, **kwargs)

    async def delete_many(self, filter: Dict[str, Any], **kwargs):
        return await self.collection.delete_many(filter, **kwargs)

    async def count_documents(self, filter: Dict[str, Any], **kwargs) -> int:
        return await self.collection.count_documents(filter, **kwargs)

    def aggregate(self, pipeline: List[Dict[str, Any]], **kwargs):
        return self.collection.aggregate(pipeline, **kwargs)


class PaymentRepository:
    _repos = {}

    @classmethod
    def get(cls, collection_name: str) -> DatabaseRepository:
        if collection_name not in cls._repos:
            cls._repos[collection_name] = DatabaseRepository(collection_name)
        return cls._repos[collection_name]
