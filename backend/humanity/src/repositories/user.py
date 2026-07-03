from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List

class UserRepository:
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        return await mongo.find_one(collection="users", query={"_id": user_id})

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        return await mongo.find_one(collection="users", query={"email": email})

    @staticmethod
    async def get_user_by_slug(slug: str) -> Optional[Dict[str, Any]]:
        return await mongo.find_one(collection="users", query={"slug": slug})

    @staticmethod
    async def create_user(user_doc: dict):
        return await mongo.insert_one(collection="users", document=user_doc)

    @staticmethod
    async def update_user(user_id: str, update_data: dict):
        return await mongo.update_one("users", {"_id": user_id}, {"$set": update_data})

    @staticmethod
    def get_users_query(query: dict):
        return mongo.find(collection="users", query=query)
