import asyncio
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import jwt
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis


BASE_URL = "http://127.0.0.1:8000"
SECRET_KEY = os.environ["SECRET_KEY"]
USER_ID = f"usage-test-{uuid.uuid4()}"
TOKEN_USER_ID = f"usage-token-test-{uuid.uuid4()}"
UPLOAD_USER_ID = f"usage-upload-test-{uuid.uuid4()}"
UPLOAD_SESSION_ID = str(uuid.uuid4())


def request(method, path, body=None, internal=True, bearer=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if internal:
        headers["X-Internal-Token"] = SECRET_KEY
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


async def main():
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    cache = redis.from_url(os.environ["REDIS_URI"], decode_responses=True)
    db = mongo[os.getenv("USAGE_DB_NAME", "doclib_usage")]
    try:
        now = datetime.now(timezone.utc)
        upload_token = jwt.encode(
            {
                "sub": f"{UPLOAD_USER_ID}@doclib.local",
                "uid": UPLOAD_USER_ID,
                "sid": UPLOAD_SESSION_ID,
                "role": "reader",
                "ai_tier": "BASIC",
                "iat": now,
                "exp": now + timedelta(minutes=15),
            },
            SECRET_KEY,
            algorithm="HS256",
        )
        await cache.sadd(f"user_sessions:{UPLOAD_USER_ID}", UPLOAD_SESSION_ID)
        assert request("GET", "/health", internal=False)[0] == 200
        assert request("GET", "/ready", internal=False)[0] == 200
        assert request("GET", f"/goi-cuoc/{USER_ID}", internal=False)[0] == 403
        status, payload = request("GET", f"/goi-cuoc/{USER_ID}")
        assert status == 200
        assert payload["data"]["ai_tier"] == "BASIC"

        await db.subscriptions.insert_one(
            {
                "user_id": USER_ID,
                "ai_tier": "PRO",
                "is_premium": True,
                "expires_at": datetime.now(timezone.utc) - timedelta(minutes=1),
            }
        )
        status, payload = request("GET", f"/goi-cuoc/{USER_ID}")
        assert status == 200
        assert payload["data"]["ai_tier"] == "BASIC"

        query = urllib.parse.urlencode(
            {"user_id": USER_ID, "role": "reader", "ai_tier": "BASIC", "feature": "chat"}
        )
        with ThreadPoolExecutor(max_workers=15) as executor:
            results = list(executor.map(lambda _: request("GET", f"/han-muc/xac-minh?{query}")[0], range(15)))
        assert results.count(200) == 10, results
        assert results.count(429) == 5, results
        assert int(await cache.get(f"quota:{USER_ID}:chat:req")) == 10

        status, _ = request(
            "POST",
            "/han-muc/su-dung",
            {"user_id": TOKEN_USER_ID, "feature": "chat", "tokens": 3000, "req_reset_hours": 24},
        )
        assert status == 200
        token_query = urllib.parse.urlencode(
            {"user_id": TOKEN_USER_ID, "role": "reader", "ai_tier": "BASIC", "feature": "chat"}
        )
        assert request("GET", f"/han-muc/xac-minh?{token_query}")[0] == 429
        assert request(
            "POST",
            "/han-muc/su-dung",
            {"user_id": TOKEN_USER_ID, "feature": "chat", "tokens": 1, "req_reset_hours": 24},
            internal=False,
        )[0] == 403
        with ThreadPoolExecutor(max_workers=8) as executor:
            upload_results = list(
                executor.map(
                    lambda _: request(
                        "POST",
                        "/han-muc/tai-len/dat-cho",
                        {"item_type": "document", "req_reset_hours": 24},
                        internal=False,
                        bearer=upload_token,
                    )[0],
                    range(8),
                )
            )
        assert upload_results.count(200) == 1, upload_results
        assert upload_results.count(429) == 7, upload_results
        assert int(await cache.get(f"quota:{UPLOAD_USER_ID}:upload_document")) == 1
        assert request(
            "GET",
            "/han-muc/tai-len/xac-minh?item_type=document",
            internal=False,
            bearer=upload_token,
        )[0] == 404
        print("usage integration passed")
    finally:
        await db.subscriptions.delete_many({"user_id": {"$in": [USER_ID, TOKEN_USER_ID]}})
        keys = []
        async for key in cache.scan_iter(match=f"quota:{USER_ID}:*"):
            keys.append(key)
        async for key in cache.scan_iter(match=f"quota:{TOKEN_USER_ID}:*"):
            keys.append(key)
        async for key in cache.scan_iter(match=f"quota:{UPLOAD_USER_ID}:*"):
            keys.append(key)
        if keys:
            await cache.delete(*keys)
        await cache.delete(f"user_sessions:{UPLOAD_USER_ID}")
        await cache.aclose()
        mongo.close()


asyncio.run(main())
