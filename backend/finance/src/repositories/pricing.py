from typing import Any, Dict, Optional

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database


class PricingRepository:
    @staticmethod
    def _content_db():
        return database.mongodb[settings.CONTENT_DB_NAME]

    @staticmethod
    def _finance_db():
        return database.mongodb[settings.FINANCE_DB_NAME]

    @classmethod
    async def get_document(
        cls,
        document_id: str,
        creator_id: str = None,
    ) -> Optional[Dict[str, Any]]:
        query = {"_id": document_id}
        if creator_id:
            query["creator_id"] = creator_id
        return await cls._content_db()["documents"].find_one(query)

    @classmethod
    async def update_document(cls, document_id: str, update_query: Dict[str, Any]):
        return await cls._content_db()["documents"].update_one(
            {"_id": document_id},
            update_query,
        )

    @classmethod
    async def get_pricing_config(cls) -> Optional[Dict[str, Any]]:
        return await cls._finance_db()["system_config"].find_one(
            {"_id": "pricing_tiers"}
        )

    @classmethod
    async def update_pricing_config(
        cls,
        update_query: Dict[str, Any],
        upsert: bool = False,
    ):
        return await cls._finance_db()["system_config"].update_one(
            {"_id": "pricing_tiers"},
            update_query,
            upsert=upsert,
        )
