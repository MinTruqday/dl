from bson import ObjectId
from pymongo import ReturnDocument

from src.core.infrastructure.mongo import mongo


class PlatformRepository:
    @staticmethod
    def identifier(value: str):
        try:
            return ObjectId(value)
        except Exception:
            return value

    @staticmethod
    async def list_ai_providers():
        return await mongo.find("ai_providers", {}).sort("_id", 1).to_list(length=None)

    @staticmethod
    async def upsert_ai_provider(provider_id: str, changes: dict, created_at):
        return await mongo.get_db()["ai_providers"].find_one_and_update(
            {"_id": provider_id},
            {"$set": changes, "$setOnInsert": {"created_at": created_at}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    @staticmethod
    async def list_ai_models(query: dict | None = None):
        return await mongo.find("ai_models", query or {}).sort("model", 1).to_list(length=None)

    @staticmethod
    async def insert_ai_model(model: dict):
        return await mongo.insert_one("ai_models", model)

    @staticmethod
    async def update_ai_model(model_id: str, changes: dict):
        return await mongo.get_db()["ai_models"].find_one_and_update(
            {"_id": PlatformRepository.identifier(model_id)},
            {"$set": changes},
            return_document=ReturnDocument.AFTER,
        )

    @staticmethod
    async def count_ai_models(model_ids: list[str], enabled: bool = True):
        identifiers = [PlatformRepository.identifier(value) for value in model_ids]
        return await mongo.count_documents(
            "ai_models", {"_id": {"$in": identifiers}, "enabled": enabled}
        )

    @staticmethod
    async def insert_admin_operation(operation: dict):
        return await mongo.insert_one("admin_operations", operation)

    @staticmethod
    async def claim_admin_operation(query: dict, timestamp, applying_status: str):
        return await mongo.get_db()["admin_operations"].find_one_and_update(
            query,
            {"$set": {"status": applying_status, "confirmed_at": timestamp}},
            return_document=ReturnDocument.AFTER,
        )

    @staticmethod
    async def complete_admin_operation(
        operation_id: str, affected: int, timestamp, completed_status: str
    ):
        return await mongo.update_one(
            "admin_operations",
            {"_id": operation_id},
            {
                "$set": {
                    "status": completed_status,
                    "affected": affected,
                    "completed_at": timestamp,
                }
            },
        )

    @staticmethod
    async def list_audit_logs(query: dict, limit: int):
        return await (
            mongo.find("audit_logs", query).sort("timestamp", -1).limit(limit).to_list(limit)
        )

    @staticmethod
    async def database_ready():
        await mongo.get_db().client.admin.command("ping")
        return True

    @staticmethod
    async def list_service_identities():
        return await mongo.find("service_identities", {}).sort("name", 1).to_list(length=None)

    @staticmethod
    async def insert_service_identity(value: dict):
        return await mongo.insert_one("service_identities", value)

    @staticmethod
    async def rotate_service_identity(identity_id: str, changes: dict, revoked_status: str):
        return await mongo.get_db()["service_identities"].find_one_and_update(
            {"_id": identity_id, "status": {"$ne": revoked_status}},
            {"$set": changes, "$inc": {"revision": 1}},
            return_document=ReturnDocument.AFTER,
        )

    @staticmethod
    async def update_service_identities(query: dict, changes: dict, many: bool = False):
        method = mongo.update_many if many else mongo.update_one
        return await method("service_identities", query, {"$set": changes})

    @staticmethod
    async def count_service_identities(query: dict):
        return await mongo.count_documents("service_identities", query)

    @staticmethod
    async def list_secret_references():
        return await mongo.find("secret_references", {}).sort("name", 1).to_list(length=None)

    @staticmethod
    async def insert_secret_reference(value: dict):
        return await mongo.insert_one("secret_references", value)

    @staticmethod
    async def rotate_secret_reference(reference_id: str, changes: dict):
        return await mongo.get_db()["secret_references"].find_one_and_update(
            {"_id": reference_id},
            {"$set": changes, "$inc": {"revision": 1}},
            return_document=ReturnDocument.AFTER,
        )

    @staticmethod
    async def delete_secret_reference(reference_id: str):
        return await mongo.delete_one("secret_references", {"_id": reference_id})
