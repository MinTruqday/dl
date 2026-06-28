from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class PricingRepository:
    @staticmethod
    def _get_db():
        return database.mongodb.get_database(settings.SERVICE_DB_NAME if hasattr(settings, "SERVICE_DB_NAME") else "doclib")

    @classmethod
    async def get_document(cls, document_id: str, creator_id: str = None) -> Optional[Dict[str, Any]]:
        query = {"_id": document_id}
        if creator_id:
            query["creator_id"] = creator_id
        return await mongo.find_one("documents", query)

    @classmethod
    async def update_document(cls, document_id: str, update_query: Dict[str, Any]):
        return await mongo.update_one("documents", {"_id": document_id}, update_query)

    @classmethod
    async def get_pricing_config(cls) -> Optional[Dict[str, Any]]:
        return await mongo.find_one("system_config", {"_id": "pricing_tiers"})

    @classmethod
    async def update_pricing_config(cls, update_query: Dict[str, Any], upsert: bool = False):
        return await mongo.update_one("system_config", {"_id": "pricing_tiers"}, update_query, upsert=upsert)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("documents", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("documents", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("documents", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("documents", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("documents", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("documents", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("documents", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("documents", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("documents", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("documents", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("documents", *args, **kwargs)
