import asyncio
import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis


BASE_URL = "http://127.0.0.1:8000"
ADMIN_ID = f"management-admin-{uuid.uuid4()}"
TARGET_ID = f"management-target-{uuid.uuid4()}"
SESSION_ID = str(uuid.uuid4())
SECRET_KEY = os.environ["SECRET_KEY"]


def call(method, path, token=None, body=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


async def main():
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    cache = redis.from_url(os.environ["REDIS_URI"], decode_responses=True)
    humanity = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    management = mongo[os.getenv("MANAGEMENT_DB_NAME", "doclib_management")]
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "management-test@doclib.local",
            "uid": ADMIN_ID,
            "sid": SESSION_ID,
            "role": "admin",
            "iat": now,
            "exp": now + timedelta(minutes=10),
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    backup_name = None
    try:
        await cache.sadd(f"user_sessions:{ADMIN_ID}", SESSION_ID)
        await humanity.users.insert_one(
            {"_id": TARGET_ID, "email": f"{TARGET_ID}@doclib.local", "role": "reader", "is_active": True, "created_at": now}
        )
        assert call("GET", "/giam-sat/thong-ke")[0] == 401
        status, payload = call("GET", "/giam-sat/thong-ke", token)
        assert status == 200
        assert payload["data"]["total_users"] >= 1

        status, payload = call("PUT", "/van-hanh/cai-dat", token, {"registration_enabled": False})
        assert status == 200
        assert payload["data"]["registration_enabled"] is False
        status, payload = call("GET", "/van-hanh/cai-dat", token)
        assert status == 200
        assert payload["data"]["registration_enabled"] is False

        assert call("POST", f"/van-hanh/nguoi-dung/{TARGET_ID}/cam-ngam", token, {"status": True})[0] == 200
        assert (await humanity.users.find_one({"_id": TARGET_ID}))["is_shadowbanned"] is True
        assert call("POST", f"/van-hanh/nguoi-dung/{TARGET_ID}/xac-minh/VERIFIED", token)[0] == 200
        assert (await humanity.users.find_one({"_id": TARGET_ID}))["kyc_status"] == "VERIFIED"

        status, payload = call("GET", "/giam-sat/kiem-tra", token)
        assert status == 200
        actions = {row.get("action") for row in payload["data"]}
        assert "user.shadowban" in actions
        assert "user.kyc" in actions
        status, payload = call("GET", "/kiem-toan/logs", token)
        assert status == 200
        assert all(row.get("actor_id") == ADMIN_ID for row in payload["data"])

        status, payload = call("POST", "/van-hanh/sao-luu", token)
        assert status == 200
        assert payload["data"]["status"] == "completed"
        backup_name = payload["data"]["object_name"]
        print("management integration passed")
    finally:
        await management.system_config.update_one(
            {"key": "registration_enabled"}, {"$set": {"value": True, "updated_at": datetime.now(timezone.utc)}}, upsert=True
        )
        await management.audit_logs.delete_many({"actor_id": ADMIN_ID})
        if backup_name:
            from src.core.storage import close_storage_client, get_storage_client

            storage = await get_storage_client()
            await storage.delete_object(Bucket=os.environ["MINIO_PRIVATE_BUCKET"], Key=backup_name)
            await management.backup_jobs.delete_one({"object_name": backup_name})
            await close_storage_client()
        await humanity.users.delete_one({"_id": TARGET_ID})
        await cache.delete(f"user_sessions:{ADMIN_ID}")
        await cache.aclose()
        mongo.close()


asyncio.run(main())
