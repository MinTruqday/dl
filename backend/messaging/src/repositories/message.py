from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings
import httpx

class MessageRepository:
    @staticmethod
    def _get_db():
        db_name = settings.MESSAGING_DB_NAME if hasattr(settings, 'MESSAGING_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("messages", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("messages", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("messages", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("messages", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("messages", *args, **kwargs)

    @classmethod
    async def update_group(cls, *args, **kwargs):
        return await mongo.update_one("message_groups", *args, **kwargs)

    @classmethod
    async def delete_group(cls, *args, **kwargs):
        return await mongo.delete_one("message_groups", *args, **kwargs)

    @classmethod
    async def insert_group(cls, *args, **kwargs):
        return await mongo.insert_one("message_groups", *args, **kwargs)

    @classmethod
    async def find_group(cls, *args, **kwargs):
        return await mongo.find_one("message_groups", *args, **kwargs)

    @classmethod
    def find_groups(cls, *args, **kwargs):
        return mongo.find("message_groups", *args, **kwargs)

    @classmethod
    async def update_setting(cls, *args, **kwargs):
        return await mongo.update_one("message_settings", *args, **kwargs)

    @classmethod
    async def find_setting(cls, *args, **kwargs):
        return await mongo.find_one("message_settings", *args, **kwargs)

    @classmethod
    async def find_shared_document(cls, *args, **kwargs):
        query = args[0] if args else kwargs.get("filter", {})
        document_id = str(query.get("_id", ""))
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.CONTENT_URL}/tai-lieu/noi-bo/truy-cap",
                json={"document_id": document_id, "user_id": "", "is_admin": True},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()["data"]

    @classmethod
    async def get_user_controls(cls, user_id: str):
        return await cls._get_db()["user_controls"].find_one({"_id": user_id})

    @classmethod
    async def update_user_controls(cls, user_id: str, update: dict):
        return await cls._get_db()["user_controls"].update_one(
            {"_id": user_id},
            update,
            upsert=True,
        )

    @classmethod
    async def claim_scheduled_message(cls, message_id: str, claimed_at):
        from pymongo import ReturnDocument

        return await cls._get_db()["messages"].find_one_and_update(
            {"_id": message_id, "is_scheduled": True},
            {
                "$set": {
                    "is_scheduled": False,
                    "created_at": claimed_at,
                    "scheduled_delivered_at": claimed_at,
                }
            },
            return_document=ReturnDocument.AFTER,
        )

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("messages", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("messages", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("messages", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("messages", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("messages", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("messages", *args, **kwargs)
