import asyncio
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import httpx
import redis.asyncio as redis_async
from motor.motor_asyncio import AsyncIOMotorClient


async def run():
    suffix = secrets.token_hex(5)
    email = f"auth-check-{suffix}@example.com"
    slug = f"auth_check_{suffix}"
    password = f"StrongPass-{suffix}-A1"
    new_password = f"ChangedPass-{suffix}-B2"
    secret = os.environ["SECRET_KEY"]
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    auth_db = mongo[os.getenv("AUTHENTICATION_DB_NAME", "doclib_authentication")]
    humanity_db = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    redis_client = redis_async.from_url(os.environ["REDIS_URI"], decode_responses=True)
    async for key in redis_client.scan_iter(match="rate_limit:*:/xac-thuc/*"):
        await redis_client.delete(key)
    user_id = None
    token = None
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            invalid = await client.post(
                "http://authentication:8000/xac-thuc/dang-ky",
                json={
                    "email": email,
                    "full_name": "Authentication Check",
                    "slug": slug,
                    "password": password,
                    "agreed_to_terms": False,
                },
            )
            assert invalid.status_code == 422, invalid.text

            register = await client.post(
                "http://authentication:8000/xac-thuc/dang-ky",
                json={
                    "email": email,
                    "full_name": "Authentication Check",
                    "slug": slug,
                    "password": password,
                    "agreed_to_terms": True,
                },
            )
            assert register.status_code == 201, register.text
            user_id = register.json()["data"]["_id"]

            blocked_internal = await client.get(
                f"http://humanity:8000/nguoi-dung/{user_id}"
            )
            assert blocked_internal.status_code == 403, blocked_internal.text

            allowed_internal = await client.get(
                f"http://humanity:8000/nguoi-dung/{user_id}",
                headers={"X-Internal-Token": secret},
            )
            assert allowed_internal.status_code == 200, allowed_internal.text

            wrong = await client.post(
                "http://authentication:8000/xac-thuc/dang-nhap",
                data={"username": email, "password": "invalid-password"},
            )
            assert wrong.status_code == 401, wrong.text

            login = await client.post(
                "http://authentication:8000/xac-thuc/dang-nhap",
                data={"username": email, "password": password},
            )
            assert login.status_code == 200, login.text
            token = login.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            profile = await client.get(
                "http://authentication:8000/xac-thuc/ca-nhan",
                headers=headers,
            )
            assert profile.status_code == 200, profile.text

            logout = await client.post(
                "http://authentication:8000/xac-thuc/dang-xuat",
                headers=headers,
            )
            assert logout.status_code == 200, logout.text

            revoked = await client.get(
                "http://authentication:8000/xac-thuc/ca-nhan",
                headers=headers,
            )
            assert revoked.status_code == 401, revoked.text

            reset_code = secrets.token_hex(12)
            reset_hash = hmac.new(
                secret.encode("utf-8"),
                reset_code.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            await auth_db.password_reset_tokens.insert_one(
                {
                    "_id": secrets.token_hex(12),
                    "email": email,
                    "token_hash": reset_hash,
                    "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
                    "used": False,
                    "created_at": datetime.now(timezone.utc),
                }
            )
            reset = await client.post(
                "http://authentication:8000/xac-thuc/dat-lai-mat-khau",
                json={"token": reset_code, "new_password": new_password},
            )
            assert reset.status_code == 200, reset.text

            reused = await client.post(
                "http://authentication:8000/xac-thuc/dat-lai-mat-khau",
                json={"token": reset_code, "new_password": password},
            )
            assert reused.status_code == 400, reused.text

            old_login = await client.post(
                "http://authentication:8000/xac-thuc/dang-nhap",
                data={"username": email, "password": password},
            )
            assert old_login.status_code == 401, old_login.text

            new_login = await client.post(
                "http://authentication:8000/xac-thuc/dang-nhap",
                data={"username": email, "password": new_password},
            )
            assert new_login.status_code == 200, new_login.text
            print("authentication integration passed")
        finally:
            if user_id:
                await auth_db.auth_credentials.delete_one({"_id": user_id})
                await auth_db.sessions.delete_many({"user_id": user_id})
                await humanity_db.users.delete_one({"_id": user_id})
            await auth_db.password_reset_tokens.delete_many({"email": email})
            await auth_db.audit_logs.delete_many({"actor_email": email})
            if user_id:
                await redis_client.delete(f"user_sessions:{user_id}")
            await redis_client.aclose()
            mongo.close()


asyncio.run(run())
