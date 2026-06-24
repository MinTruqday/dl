from src.core.api_client import db_client
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database


class IdentityRepository:
    @staticmethod
    async def get_system_config(db=None) -> Optional[Dict[str, Any]]:
        if db is None:
            db = database.mongodb[
                (
                    settings.SERVICE_DB_NAME
                    if hasattr(database, "settings")
                    else "doclib"
                )
            ]
        return await db_client.find_one(collection="settings", query={"_id": "system_config"})

    @staticmethod
    async def create_auth_credential(auth_cred: dict, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        return await db_client.insert_one(collection="auth_credentials", document=auth_cred)

    @staticmethod
    async def insert_audit_log(log_data: dict, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        return await db_client.insert_one(collection="audit_logs", document=log_data)

    @staticmethod
    async def get_auth_credential_by_id(
        user_id: str, db=None
    ) -> Optional[Dict[str, Any]]:
        if db is None:
            db = database.mongodb.get_default_database()
        return await db_client.find_one(collection="auth_credentials", query={"_id": user_id})

    @staticmethod
    async def get_auth_credential_by_email(
        email: str, db=None
    ) -> Optional[Dict[str, Any]]:
        if db is None:
            db = database.mongodb.get_default_database()
        return await db_client.find_one(collection="auth_credentials", query={"email": email})

    @staticmethod
    async def update_password_hash(email: str, password_hash: str, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        return await db["auth_credentials"].update_one(
            {"email": email},
            {"$set": {"password_hash": password_hash}},
        )

    @staticmethod
    async def create_password_reset_token(token_data: dict, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        return await db_client.insert_one(collection="password_reset_tokens", document=token_data)

    @staticmethod
    async def get_valid_password_reset_token(
        token: str, db=None
    ) -> Optional[Dict[str, Any]]:
        if db is None:
            db = database.mongodb.get_default_database()
        return await db["password_reset_tokens"].find_one(
            {"token": token, "used": False}
        )

    @staticmethod
    async def mark_password_reset_token_used(token_id: str, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        return await db["password_reset_tokens"].update_one(
            {"_id": token_id}, {"$set": {"used": True}}
        )

    @staticmethod
    async def upsert_passkey_challenge(email: str, challenge: str, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        return await db["passkey_challenges"].update_one(
            {"_id": f"auth:{email}"},
            {
                "$set": {
                    "challenge": challenge,
                    "created_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

    @staticmethod
    async def get_passkey_challenge(email: str, db=None) -> Optional[Dict[str, Any]]:
        if db is None:
            db = database.mongodb.get_default_database()
        return await db_client.find_one(collection="passkey_challenges", query={"_id": f"auth:{email}"})

    @staticmethod
    async def delete_passkey_challenge(email: str, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        return await db_client.delete_one(collection="passkey_challenges", filter={"_id": f"auth:{email}"})

    @staticmethod
    async def update_passkey_sign_count(
        user_id: str, credential_id: str, sign_count: int, db=None
    ):
        if db is None:
            db = database.mongodb.get_default_database()
        return await db["auth_credentials"].update_one(
            {"_id": user_id, "passkeys.credential_id": credential_id},
            {"$set": {"passkeys.$.sign_count": sign_count}},
        )

    @staticmethod
    async def register_session(user_id: str, session_id: str, client_ip: str):
        if database.redis:
            await database.redis.sadd(f"user_sessions:{user_id}", session_id)
            await database.redis.setex(f"session_meta:{session_id}", 604800, client_ip)

    @staticmethod
    async def revoke_all_sessions(user_id: str):
        if not database.redis:
            return
        session = await database.redis.smembers(f"user_sessions:{user_id}")
        for sid in session:
            await database.redis.delete(f"session_meta:{sid}")
        await database.redis.delete(f"user_sessions:{user_id}")

    @staticmethod
    async def set_redis_passkey_challenge(email: str, challenge: str):
        if database.redis:
            await database.redis.setex(
                f"passkey_auth_challenge:{email}", 300, challenge
            )

    @staticmethod
    async def get_redis_passkey_challenge(email: str) -> Optional[str]:
        if database.redis:
            val = await database.redis.get(f"passkey_auth_challenge:{email}")
            if isinstance(val, bytes):
                return val.decode("utf-8")
            return val
        return None

    @staticmethod
    async def delete_redis_passkey_challenge(email: str):
        if database.redis:
            await database.redis.delete(f"passkey_auth_challenge:{email}")
