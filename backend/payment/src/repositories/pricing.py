from src.core.infrastructure.mongo_client import mongo_client
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
        return await mongo_client.find_one("documents", query)

    @classmethod
    async def update_document(cls, document_id: str, update_query: Dict[str, Any]):
        return await mongo_client.update_one("documents", {"_id": document_id}, update_query)

    @classmethod
    async def get_pricing_config(cls) -> Optional[Dict[str, Any]]:
        return await mongo_client.find_one("system_config", {"_id": "pricing_tiers"})

    @classmethod
    async def update_pricing_config(cls, update_query: Dict[str, Any], upsert: bool = False):
        return await mongo_client.update_one("system_config", {"_id": "pricing_tiers"}, update_query, upsert=upsert)
