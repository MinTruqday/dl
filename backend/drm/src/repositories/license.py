from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings
class LicenseRepository:
    @staticmethod
    def _get_db():
        return database.mongodb.get_database(settings.DRM_DB_NAME if hasattr(settings, 'DRM_DB_NAME') else "doclib")

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
        content_db = database.mongodb["doclib_content"]
        return await content_db["documents"].find_one({"_id": document_id})

    @classmethod
    async def get_purchase(cls, user_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        return await mongo.find_one("purchases", {"user_id": user_id, "item_id": item_id})

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
