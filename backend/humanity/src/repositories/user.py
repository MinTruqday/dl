from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List

class UserRepository:
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        return await mongo.find_one(collection="users", query={"_id": user_id})

    @staticmethod
    async def get_users_by_ids(user_ids: List[str]) -> List[Dict[str, Any]]:
        return await mongo.find(collection="users", query={"_id": {"$in": user_ids}}).to_list(length=None)

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        return await mongo.find_one(collection="users", query={"email": email.lower()})

    @staticmethod
    async def get_user_by_slug(slug: str) -> Optional[Dict[str, Any]]:
        return await mongo.find_one(collection="users", query={"slug": slug.lower()})

    @staticmethod
    async def create_user(user_doc: dict):
        return await mongo.insert_one(collection="users", document=user_doc)

    @staticmethod
    async def update_user(user_id: str, update_data: dict):
        update = update_data if any(key.startswith("$") for key in update_data) else {"$set": update_data}
        return await mongo.update_one("users", {"_id": user_id}, update)

    @staticmethod
    async def delete_user(user_id: str):
        return await mongo.delete_one("users", {"_id": user_id})

    @staticmethod
    def get_users_query(query: dict):
        return mongo.find(collection="users", query=query)
