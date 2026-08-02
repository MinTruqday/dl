from typing import Any, Dict, Optional

from pymongo import ReturnDocument

from src.core.infrastructure.mongo import mongo
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings
from src.services.content_client import ContentClient
from src.services.finance_client import FinanceClient
class LicenseRepository:
    @staticmethod
    def _get_db():
        return database.mongodb.get_database(settings.DRM_DB_NAME)

    @classmethod
    async def find_license_by_file_id(cls, file_id: str) -> Optional[Dict[str, Any]]:
        return await mongo.find_one("drm_licenses", {"file_id": file_id})
        
    @classmethod
    async def create_license(cls, license_doc: Dict[str, Any]):
        return await mongo.insert_one("drm_licenses", license_doc)

    @classmethod
    async def update_license(cls, license_id, update_query: Dict[str, Any]):
        return await mongo.update_one("drm_licenses", {"_id": license_id}, update_query)

    @classmethod
    async def get_document(cls, document_id: str) -> Optional[Dict[str, Any]]:
        return await ContentClient.get(document_id)

    @classmethod
    async def get_purchase(cls, user_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        return await FinanceClient.get_purchase(user_id, item_id)

    @classmethod
    async def get_drm_settings(cls, document_id: str) -> Optional[Dict[str, Any]]:
        return await mongo.find_one(
            "document_drm_settings", {"document_id": document_id}
        )

    @classmethod
    async def claim_access(
        cls,
        license_id: Any,
        hardware_signature: str,
        accessed_at,
        client_ip: str,
    ) -> Optional[Dict[str, Any]]:
        return await cls._get_db()["drm_licenses"].find_one_and_update(
            {
                "_id": license_id,
                "status": "ACTIVE",
                "$and": [
                    {
                        "$or": [
                            {"hardware_signature": {"$exists": False}},
                            {"hardware_signature": None},
                            {"hardware_signature": hardware_signature},
                        ]
                    },
                    {
                        "$or": [
                            {"expires_at": {"$exists": False}},
                            {"expires_at": {"$gt": accessed_at}},
                        ]
                    },
                    {
                        "$or": [
                            {"max_open_count": {"$exists": False}},
                            {"$expr": {"$lt": ["$open_count", "$max_open_count"]}},
                        ]
                    },
                ],
            },
            {
                "$set": {
                    "hardware_signature": hardware_signature,
                    "last_opened_at": accessed_at,
                },
                "$inc": {"open_count": 1},
                "$push": {
                    "recent_accesses": {
                        "$each": [{"time": accessed_at, "ip": client_ip}],
                        "$slice": -20,
                    }
                },
            },
            return_document=ReturnDocument.AFTER,
        )

    @classmethod
    async def record_audit_log(cls, log_doc: Dict[str, Any]):
        return await mongo.insert_one("audit_logs", log_doc)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("drm_licenses", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("drm_licenses", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("drm_licenses", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("drm_licenses", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("drm_licenses", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("drm_licenses", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("drm_licenses", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("drm_licenses", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("drm_licenses", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("drm_licenses", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("drm_licenses", *args, **kwargs)
