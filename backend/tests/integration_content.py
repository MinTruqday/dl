import asyncio
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis


BASE_URL = "http://127.0.0.1:8000"
AUTHOR_ID = f"content-author-{uuid.uuid4()}"
BUYER_ID = f"content-buyer-{uuid.uuid4()}"
AUTHOR_SESSION = str(uuid.uuid4())
BUYER_SESSION = str(uuid.uuid4())
SECRET_KEY = os.environ["SECRET_KEY"]


def token(user_id, session_id, role):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": f"{user_id}@doclib.local", "uid": user_id, "sid": session_id, "role": role, "full_name": user_id, "iat": now, "exp": now + timedelta(minutes=15)},
        SECRET_KEY,
        algorithm="HS256",
    )


def call(method, path, bearer=None, body=None, headers=None):
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    if bearer:
        request_headers["Authorization"] = f"Bearer {bearer}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


async def main():
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    cache = redis.from_url(os.environ["REDIS_URI"], decode_responses=True)
    content = mongo[os.getenv("CONTENT_DB_NAME", "doclib_content")]
    finance = mongo[os.getenv("FINANCE_DB_NAME", "doclib_finance")]
    humanity = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    notification = mongo[os.getenv("NOTIFICATION_DB_NAME", "doclib_notification")]
    author_token = token(AUTHOR_ID, AUTHOR_SESSION, "author")
    buyer_token = token(BUYER_ID, BUYER_SESSION, "reader")
    document_ids = []
    try:
        await cache.sadd(f"user_sessions:{AUTHOR_ID}", AUTHOR_SESSION)
        await cache.sadd(f"user_sessions:{BUYER_ID}", BUYER_SESSION)
        await humanity.users.insert_many(
            [
                {"_id": AUTHOR_ID, "email": f"{AUTHOR_ID}@doclib.local", "full_name": AUTHOR_ID, "slug": AUTHOR_ID, "role": "author", "is_active": True, "created_at": datetime.now(timezone.utc)},
                {"_id": BUYER_ID, "email": f"{BUYER_ID}@doclib.local", "full_name": BUYER_ID, "slug": BUYER_ID, "role": "reader", "is_active": True, "created_at": datetime.now(timezone.utc)},
            ]
        )
        assert call("GET", "/ready")[0] == 200
        assert call("POST", "/tai-lieu", buyer_token, {"title": "Denied", "content": "x"})[0] == 403

        status, payload = call(
            "POST",
            "/tai-lieu",
            author_token,
            {"title": "Paid Integration Document", "content": "initial", "content_format": "markdown", "price_dl": 100, "preview_pages": 0, "visibility": "public"},
        )
        assert status == 201, payload
        document_id = payload["data"]["_id"]
        document_ids.append(document_id)
        assert payload["data"]["slug"]
        long_content = "protected-content-" * 500
        status, payload = call("PUT", f"/tai-lieu/{document_id}/noi-dung", author_token, {"content": long_content, "content_format": "markdown"})
        assert status == 200, payload
        status, payload = call("POST", f"/xuat-ban/{document_id}", author_token)
        assert status == 200, payload
        for _ in range(100):
            published = await content.documents.find_one(
                {"_id": document_id},
                {"status": 1},
            )
            if published and published.get("status") == "published":
                break
            await asyncio.sleep(0.1)
        assert published and published.get("status") == "published", published

        status, payload = call("GET", f"/tai-lieu/{document_id}")
        assert status == 200
        assert payload["data"].get("content") == ""
        assert "content_fragments" not in payload["data"]
        assert "access_password_hash" not in payload["data"]
        assert call("GET", f"/tai-lieu/{document_id}/khoa-giai-ma")[0] == 403

        status, payload = call("GET", f"/tai-lieu/{document_id}", buyer_token)
        assert status == 200
        assert "content_fragments" not in payload["data"]
        await finance.purchases.insert_one({"_id": str(uuid.uuid4()), "user_id": BUYER_ID, "item_id": document_id, "status": "purchased", "created_at": datetime.now(timezone.utc)})
        status, payload = call("GET", f"/tai-lieu/{document_id}", buyer_token)
        assert status == 200, payload
        fragment = payload["data"]["content_fragments"][0]
        assert "content" not in payload["data"]
        status, key_payload = call("GET", f"/tai-lieu/{document_id}/khoa-giai-ma", buyer_token)
        assert status == 200
        raw = base64.b64decode(fragment)
        plaintext = AESGCM(base64.b64decode(key_payload["data"]["key"])).decrypt(raw[:12], raw[12:], None).decode()
        assert plaintext == long_content[:50000]

        status, payload = call("POST", f"/phien-ban/luu/{document_id}?version_note=integration", author_token)
        assert status == 201
        status, payload = call("GET", f"/phien-ban/tai-lieu/{document_id}", author_token)
        assert status == 200
        assert len(payload["data"]) == 1

        status, payload = call("POST", "/thu-vien/danh-sach", buyer_token, {"name": "Integration List", "description": "test", "is_public": False})
        assert status == 201
        list_id = payload["data"]["_id"]
        assert call("POST", f"/thu-vien/lists/{list_id}/documents/{document_id}", buyer_token)[0] == 200
        status, payload = call("GET", f"/thu-vien/danh-sach/{list_id}", buyer_token)
        assert status == 200
        assert payload["data"]["documents_detailed"][0]["_id"] == document_id

        status, payload = call("POST", f"/noi-bat/tai-lieu/{document_id}", buyer_token, {"text": "protected", "start_offset": 0, "end_offset": 9, "note": "integration"})
        assert status == 201
        highlight_id = payload["data"]["_id"]
        assert call("DELETE", f"/noi-bat/{highlight_id}", buyer_token)[0] == 200
        print("content integration passed")
    finally:
        await content.documents.delete_many({"_id": {"$in": document_ids}})
        await content.document_versions.delete_many({"creator_id": AUTHOR_ID})
        await content.document_revisions.delete_many({"creator_id": AUTHOR_ID})
        await content.reading_lists.delete_many({"user_id": BUYER_ID})
        await content.highlights.delete_many({"user_id": BUYER_ID})
        await finance.purchases.delete_many({"user_id": BUYER_ID, "item_id": {"$in": document_ids}})
        await humanity.users.delete_many({"_id": {"$in": [AUTHOR_ID, BUYER_ID]}})
        await notification.announcements.delete_many({"target_user_id": AUTHOR_ID})
        await cache.delete(f"user_sessions:{AUTHOR_ID}", f"user_sessions:{BUYER_ID}")
        async for key in cache.scan_iter(match=f"*:{document_ids[0] if document_ids else 'none'}:*"):
            await cache.delete(key)
        await cache.aclose()
        mongo.close()


asyncio.run(main())
