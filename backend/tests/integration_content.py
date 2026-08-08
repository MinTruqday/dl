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


BASE_URL = os.getenv("CONTENT_TEST_URL", "http://traefik:8000")
AUTHOR_ID = f"content-author-{uuid.uuid4()}"
BUYER_ID = f"content-buyer-{uuid.uuid4()}"
ADMIN_ID = f"content-admin-{uuid.uuid4()}"
AUTHOR_SESSION = str(uuid.uuid4())
BUYER_SESSION = str(uuid.uuid4())
ADMIN_SESSION = str(uuid.uuid4())
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
    engagement = mongo[os.getenv("ENGAGEMENT_DB_NAME", "doclib_engagement")]
    finance = mongo[os.getenv("FINANCE_DB_NAME", "doclib_finance")]
    humanity = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    notification = mongo[os.getenv("NOTIFICATION_DB_NAME", "doclib_notification")]
    author_token = token(AUTHOR_ID, AUTHOR_SESSION, "author")
    buyer_token = token(BUYER_ID, BUYER_SESSION, "reader")
    admin_token = token(ADMIN_ID, ADMIN_SESSION, "admin")
    document_ids = []
    try:
        await cache.sadd(f"user_sessions:{AUTHOR_ID}", AUTHOR_SESSION)
        await cache.sadd(f"user_sessions:{BUYER_ID}", BUYER_SESSION)
        await cache.sadd(f"user_sessions:{ADMIN_ID}", ADMIN_SESSION)
        await humanity.users.insert_many(
            [
                {"_id": AUTHOR_ID, "email": f"{AUTHOR_ID}@doclib.local", "full_name": AUTHOR_ID, "slug": AUTHOR_ID, "role": "author", "is_active": True, "created_at": datetime.now(timezone.utc)},
                {"_id": BUYER_ID, "email": f"{BUYER_ID}@doclib.local", "full_name": BUYER_ID, "slug": BUYER_ID, "role": "reader", "is_active": True, "created_at": datetime.now(timezone.utc)},
                {"_id": ADMIN_ID, "email": f"{ADMIN_ID}@doclib.local", "full_name": ADMIN_ID, "slug": ADMIN_ID, "role": "admin", "is_active": True, "created_at": datetime.now(timezone.utc)},
            ]
        )
        with urllib.request.urlopen("http://content:8000/ready", timeout=20) as ready:
            assert ready.status == 200
        assert call("POST", "/tai-lieu", buyer_token, {"title": "Denied", "content": "x"})[0] == 403

        status, payload = call(
            "POST",
            "/tai-lieu",
            author_token,
            {"title": "Paid Integration Document", "content": "initial", "content_format": "markdown", "price_dl": 100, "preview_pages": 0, "visibility": "public"},
        )
        assert status == 201, payload
        document_id = payload["data"]["_id"]
        stale_version = payload["data"]["updated_at"]
        document_slug = payload["data"]["slug"]
        document_ids.append(document_id)
        assert payload["data"]["slug"]
        assert call("GET", f"/tai-lieu/xem-truoc/{document_slug}")[0] == 404
        long_content = "protected-content-" * 500
        status, payload = call("PUT", f"/tai-lieu/{document_id}/noi-dung", author_token, {"content": long_content, "content_format": "markdown"})
        assert status == 200, payload
        status, payload = call(
            "PUT",
            f"/tai-lieu/{document_id}/noi-dung",
            author_token,
            {
                "content": "stale update",
                "content_format": "markdown",
                "expected_version": stale_version,
            },
        )
        assert status == 409, payload
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
        recommended_id = f"content-recommended-{uuid.uuid4()}"
        document_ids.append(recommended_id)
        await content.documents.update_one(
            {"_id": document_id},
            {"$set": {"tags": ["agentic"], "category": "technology"}},
        )
        await content.documents.insert_one(
            {
                "_id": recommended_id,
                "title": "Personalized Integration Document",
                "slug": recommended_id,
                "creator_id": AUTHOR_ID,
                "content": "personalized",
                "content_format": "markdown",
                "status": "published",
                "visibility": "public",
                "is_deleted": False,
                "tags": ["agentic"],
                "category": "technology",
                "views": 1,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        )
        await engagement.reading_history.insert_one(
            {
                "_id": str(uuid.uuid4()),
                "user_id": BUYER_ID,
                "document_id": document_id,
                "progress_percentage": 80,
                "last_read_at": datetime.now(timezone.utc),
            }
        )
        await engagement.user_content_profiles.update_one(
            {"_id": BUYER_ID},
            {"$addToSet": {"bookmarks": document_id}},
            upsert=True,
        )
        await content.audit_logs.insert_one(
            {
                "_id": str(uuid.uuid4()),
                "document_id": document_id,
                "actor_id": AUTHOR_ID,
                "action": "integration",
                "reason": "integration",
                "timestamp": datetime.now(timezone.utc),
            }
        )
        status, analytics_payload = call(
            "GET",
            f"/tai-lieu/{document_id}/thong-ke",
            author_token,
        )
        assert status == 200, analytics_payload
        assert analytics_payload["data"]["saves"] == 1
        assert analytics_payload["data"]["reads"] == 1
        status, audit_payload = call(
            "GET",
            f"/tai-lieu/{document_id}/nhat-ky-hoat-dong",
            author_token,
        )
        assert status == 200, audit_payload
        assert audit_payload["data"][0]["action"] == "integration"
        status, taxonomy_payload = call("GET", "/kham-pha/the-loai")
        assert status == 200, taxonomy_payload
        assert "technology" in taxonomy_payload["data"]["categories"]
        assert "agentic" in taxonomy_payload["data"]["tags"]
        status, history_payload = call("GET", "/doc-hieu/lich-su", buyer_token)
        assert status == 200, history_payload
        assert history_payload["data"][0]["document_title"] == "Paid Integration Document"
        status, recommendation_payload = call(
            "GET",
            "/kham-pha/goi-y-ca-nhan?limit=10",
            buyer_token,
        )
        assert status == 200, recommendation_payload
        recommendation_ids = [
            item["_id"] for item in recommendation_payload["data"]
        ]
        assert recommended_id in recommendation_ids, recommendation_payload
        assert document_id not in recommendation_ids, recommendation_payload
        await content.documents.update_one(
            {"_id": recommended_id},
            {"$set": {"status": "processing_publish"}},
        )
        status, queue_payload = call(
            "GET",
            "/tai-lieu/hang-doi-duyet",
            admin_token,
        )
        assert status == 200, queue_payload
        assert any(row["_id"] == recommended_id for row in queue_payload["data"])
        await content.documents.update_one(
            {"_id": recommended_id},
            {"$set": {"status": "published"}},
        )
        assert call("GET", "/kham-pha/goi-y-ai?limit=10")[0] == 404
        search_query = urllib.parse.quote("Paid Integration")
        status, search_payload = call(
            "GET",
            f"/tim-kiem/thong-minh?q={search_query}&limit=10",
        )
        assert status == 200, search_payload
        assert any(
            item["_id"] == document_id for item in search_payload["data"]
        ), search_payload

        status, payload = call("GET", f"/tai-lieu/{document_id}")
        assert status == 200
        assert payload["data"].get("content") == ""
        assert "content_fragments" not in payload["data"]
        assert "access_password_hash" not in payload["data"]
        assert call("GET", f"/tai-lieu/{document_id}/khoa-giai-ma")[0] == 403

        status, payload = call("GET", f"/tai-lieu/{document_id}", buyer_token)
        assert status == 200
        assert "content_fragments" not in payload["data"]
        search_inside = urllib.parse.quote("protected")
        assert call(
            "GET",
            f"/doc-hieu/tai-lieu/{document_id}/tim-kiem?q={search_inside}",
            buyer_token,
        )[0] == 403
        assert call(
            "GET",
            f"/tai-lieu/{document_id}/chi-so-hoc-thuat",
            buyer_token,
        )[0] == 403
        await finance.purchases.insert_one({"_id": str(uuid.uuid4()), "user_id": BUYER_ID, "item_id": document_id, "status": "purchased", "created_at": datetime.now(timezone.utc)})
        assert call(
            "GET",
            f"/tai-lieu/{document_id}/chi-so-hoc-thuat",
            buyer_token,
        )[0] == 200
        status, payload = call("GET", f"/tai-lieu/{document_id}", buyer_token)
        assert status == 200, payload
        fragment = payload["data"]["content_fragments"][0]
        assert "content" not in payload["data"]
        status, key_payload = call("GET", f"/tai-lieu/{document_id}/khoa-giai-ma", buyer_token)
        assert status == 200
        raw = base64.b64decode(fragment)
        plaintext = AESGCM(base64.b64decode(key_payload["data"]["key"])).decrypt(raw[:12], raw[12:], None).decode()
        assert plaintext == long_content[:50000]
        status, inside_payload = call(
            "GET",
            f"/doc-hieu/tai-lieu/{document_id}/tim-kiem?q={search_inside}",
            buyer_token,
        )
        assert status == 200, inside_payload
        assert inside_payload["data"]["total"] > 0
        status, preview_payload = call("GET", f"/tai-lieu/xem-truoc/{document_slug}")
        assert status == 200, preview_payload
        assert "preview_content" in preview_payload["data"]

        status, payload = call("POST", f"/phien-ban/luu/{document_id}?version_note=integration", author_token)
        assert status == 201
        status, payload = call("GET", f"/phien-ban/tai-lieu/{document_id}", author_token)
        assert status == 200
        assert len(payload["data"]) == 1
        status, payload = call(
            "PUT",
            f"/tai-lieu/{document_id}",
            author_token,
            {"title": "Updated Integration Document"},
        )
        assert status == 200 and payload["data"]["title"] == "Updated Integration Document", payload
        assert call("DELETE", f"/tai-lieu/{document_id}", buyer_token)[0] == 403
        status, payload = call(
            "DELETE",
            f"/tai-lieu/{document_id}",
            author_token,
        )
        assert status == 200, payload
        deleted = await content.documents.find_one({"_id": document_id})
        assert deleted and deleted["is_deleted"] is True, deleted
        status, payload = call(
            "POST",
            f"/tai-lieu/{document_id}/khoi-phuc",
            author_token,
        )
        assert status == 200, payload
        restored = await content.documents.find_one({"_id": document_id})
        assert restored and restored["is_deleted"] is False, restored

        status, payload = call("POST", "/thu-vien/danh-sach", buyer_token, {"name": "Integration List", "description": "test", "is_public": False})
        assert status == 201
        list_id = payload["data"]["_id"]
        assert call("POST", f"/thu-vien/lists/{list_id}/documents/{document_id}", buyer_token)[0] == 200
        status, payload = call("GET", f"/thu-vien/danh-sach/{list_id}", buyer_token)
        assert status == 200
        assert payload["data"]["documents_detailed"][0]["_id"] == document_id
        assert await engagement.reading_lists.find_one({"_id": list_id})
        assert not await content.reading_lists.find_one({"_id": list_id})

        status, payload = call("POST", f"/noi-bat/tai-lieu/{document_id}", buyer_token, {"text": "protected", "start_offset": 0, "end_offset": 9, "note": "integration"})
        assert status == 201
        highlight_id = payload["data"]["_id"]
        assert call("DELETE", f"/noi-bat/{highlight_id}", buyer_token)[0] == 200
        print("content integration passed")
    finally:
        await content.documents.delete_many({"_id": {"$in": document_ids}})
        await content.document_versions.delete_many({"creator_id": AUTHOR_ID})
        await content.document_revisions.delete_many({"creator_id": AUTHOR_ID})
        await engagement.reading_lists.delete_many({"user_id": BUYER_ID})
        await engagement.reading_history.delete_many({"user_id": BUYER_ID})
        await engagement.user_content_profiles.delete_many({"_id": BUYER_ID})
        await engagement.highlights.delete_many({"user_id": BUYER_ID})
        await finance.purchases.delete_many({"user_id": BUYER_ID, "item_id": {"$in": document_ids}})
        await humanity.users.delete_many({"_id": {"$in": [AUTHOR_ID, BUYER_ID, ADMIN_ID]}})
        await content.audit_logs.delete_many({"document_id": {"$in": document_ids}})
        await notification.announcements.delete_many({"target_user_id": AUTHOR_ID})
        await cache.delete(
            f"user_sessions:{AUTHOR_ID}",
            f"user_sessions:{BUYER_ID}",
            f"user_sessions:{ADMIN_ID}",
        )
        async for key in cache.scan_iter(match=f"*:{document_ids[0] if document_ids else 'none'}:*"):
            await cache.delete(key)
        await cache.aclose()
        mongo.close()


asyncio.run(main())
