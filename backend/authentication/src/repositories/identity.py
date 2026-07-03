from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any

class IdentityRepository:
    @staticmethod
    async def get_system_config():
        return await mongo.find_one("system_configs", {"type": "registration"})

    @staticmethod
    async def get_auth_credential_by_id(user_id: str):
        return await mongo.find_one("auth_credentials", {"_id": user_id})

    @staticmethod
    async def get_auth_credential_by_email(email: str):
        return await mongo.find_one("auth_credentials", {"email": email})
        
    @staticmethod
    async def get_auth_credential_by_slug(slug: str):
        return await mongo.find_one("auth_credentials", {"slug": slug})

    @staticmethod
    async def create_auth_credential(cred_data: dict):
        return await mongo.insert_one("auth_credentials", cred_data)

    @staticmethod
    async def insert_audit_log(log_data: dict):
        return await mongo.insert_one("audit_logs", log_data)

    @staticmethod
    async def register_session(user_id: str, session_id: str, ip: str):
        return await mongo.insert_one("sessions", {"_id": session_id, "user_id": user_id, "ip": ip})
