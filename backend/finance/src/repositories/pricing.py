from typing import Any, Dict, Optional

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.services.content_client import ContentClient


class PricingRepository:
    @staticmethod
    def _finance_db():
        return database.mongodb[settings.FINANCE_DB_NAME]

    @classmethod
    async def get_document(
        cls,
        document_id: str,
        creator_id: str = None,
    ) -> Optional[Dict[str, Any]]:
        document = await ContentClient.get(document_id)
        if creator_id and document and document.get("creator_id") != creator_id:
            return None
        return document

    @classmethod
    async def update_document(
        cls,
        document_id: str,
        update_query: Dict[str, Any],
        actor_id: str,
        is_admin: bool = False,
    ):
        values = update_query.get("$set", {})
        return await ContentClient.update_pricing(
            document_id,
            actor_id,
            is_admin,
            int(values.get("price_dl", 0)),
            bool(values.get("is_drm_protected", True)),
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
