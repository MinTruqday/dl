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
ADMIN_ID = f"audit-admin-{uuid.uuid4()}"
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
    management = mongo[os.getenv("MANAGEMENT_DB_NAME", "doclib_management")]
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "audit-test@doclib.local",
            "uid": ADMIN_ID,
            "sid": SESSION_ID,
            "role": "admin",
            "iat": now,
            "exp": now + timedelta(minutes=10),
        },
        SECRET_KEY,
        algorithm="HS256",
    )

    test_logs = [
        {
            "_id": f"audit-log-1-{uuid.uuid4()}",
            "actor_id": ADMIN_ID,
            "actor_email": "admin@doclib.local",
            "module": "management",
            "action": "system.config",
            "severity": "CRITICAL",
            "status": "SUCCESS",
            "target_type": "system",
            "target_id": "system_config",
            "ip_address": "127.0.0.1",
            "timestamp": now,
        },
        {
            "_id": f"audit-log-2-{uuid.uuid4()}",
            "actor_id": ADMIN_ID,
            "actor_email": "admin@doclib.local",
            "module": "drm",
            "action": "license.revoke",
            "severity": "WARNING",
            "status": "SUCCESS",
            "target_type": "license",
            "target_id": "lic_123",
            "ip_address": "127.0.0.1",
            "timestamp": now,
        },
        {
            "_id": f"audit-log-3-{uuid.uuid4()}",
            "actor_id": "suspicious-user-1",
            "actor_email": "intruder@external.local",
            "module": "authentication",
            "action": "user.login_failed",
            "severity": "SECURITY",
            "status": "FAILED",
            "target_type": "user",
            "target_id": "suspicious-user-1",
            "ip_address": "192.168.1.100",
            "timestamp": now,
        },
    ]

    try:
        await cache.sadd(f"user_sessions:{ADMIN_ID}", SESSION_ID)
        await management.audit_logs.insert_many(test_logs)

        unauth_status, _ = call("GET", "/kiem-toan/nhat-ky")
        assert unauth_status == 401

        status, payload = call("GET", "/kiem-toan/nhat-ky?page=1&page_size=10", token)
        assert status == 200
        assert "items" in payload["data"]
        assert payload["data"]["total"] >= 3

        status, payload = call("GET", "/kiem-toan/nhat-ky?module=drm", token)
        assert status == 200
        assert all(row.get("module") == "drm" for row in payload["data"]["items"])

        status, payload = call("GET", "/kiem-toan/nhat-ky?severity=SECURITY", token)
        assert status == 200
        assert all(row.get("severity") == "SECURITY" for row in payload["data"]["items"])

        status, payload = call("GET", "/kiem-toan/nhat-ky?search=intruder", token)
        assert status == 200
        assert len(payload["data"]["items"]) >= 1

        status, payload = call("GET", "/kiem-toan/thong-ke", token)
        assert status == 200
        stats_data = payload["data"]
        assert stats_data["total_events"] >= 3
        assert stats_data["security_alerts"] >= 1
        assert stats_data["failed_operations"] >= 1

        status, payload = call("GET", "/kiem-toan/ket-xuat?format=json", token)
        assert status == 200
        assert payload["data"]["format"] == "json"
        assert payload["data"]["total_exported"] >= 3

        status, payload = call("GET", "/kiem-toan/ket-xuat?format=csv", token)
        assert status == 200
        assert payload["data"]["format"] == "csv"
        assert "id,timestamp,actor_id" in payload["data"]["content"]

        status, payload = call("GET", "/kiem-toan/kiem-tra-toan-ven", token)
        assert status == 200
        assert payload["data"]["verified"] is True
        assert payload["data"]["status"] == "SECURE"

        status, payload = call("GET", "/kiem-toan/logs", token)
        assert status == 200
        assert isinstance(payload["data"], list)

        print("AUDIT_INTEGRATION_TEST_PASSED_SUCCESSFULLY")
    finally:
        await management.audit_logs.delete_many({"_id": {"$in": [l["_id"] for l in test_logs]}})
        await cache.delete(f"user_sessions:{ADMIN_ID}")
        await cache.aclose()
        mongo.close()


asyncio.run(main())
