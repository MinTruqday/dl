import asyncio
import base64
import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import redis.asyncio as redis
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from motor.motor_asyncio import AsyncIOMotorClient


SECRET_KEY = os.environ["SECRET_KEY"]
USER_ID = f"plat-user-{uuid.uuid4().hex[:12]}"
OTHER_USER_ID = f"plat-other-{uuid.uuid4().hex[:12]}"
USER_SESSION = str(uuid.uuid4())
OTHER_SESSION = str(uuid.uuid4())
DOCUMENT_ID = f"plat-document-{uuid.uuid4()}"
FILE_ID = f"plat-file-{uuid.uuid4()}"
LICENSE_ID = f"plat-license-{uuid.uuid4()}"


def create_token(user_id: str, session_id: str, role: str = "author") -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": f"{user_id}@example.com",
            "uid": user_id,
            "sid": session_id,
            "role": role,
            "ai_tier": "BASIC",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        SECRET_KEY,
        algorithm="HS256",
    )


def call(
    service: str,
    method: str,
    path: str,
    body=None,
    bearer: str | None = None,
    internal: bool = False,
):
    headers = {"Content-Type": "application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    if internal:
        headers["X-Internal-Token"] = SECRET_KEY
    request = urllib.request.Request(
        f"http://{service}:8000{path}",
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read()
        return error.code, json.loads(raw) if raw else None


async def main():
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    cache = redis.from_url(os.environ["REDIS_URI"], decode_responses=True)
    humanity = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    notification = mongo[os.getenv("NOTIFICATION_DB_NAME", "doclib_notification")]
    content = mongo[os.getenv("CONTENT_DB_NAME", "doclib_content")]
    drm = mongo[os.getenv("DRM_DB_NAME", "doclib_drm")]
    user_token = create_token(USER_ID, USER_SESSION)
    other_token = create_token(OTHER_USER_ID, OTHER_SESSION)
    raw_key = os.urandom(32)
    notification_id = None
    try:
        for service in ["humanity", "notification", "drm"]:
            assert call(service, "GET", "/ready")[0] == 200

        user_payload = {
            "email": f"{USER_ID}@example.com",
            "full_name": "Platform User",
            "slug": USER_ID,
            "role": "author",
        }
        assert call("humanity", "POST", "/nguoi-dung/", user_payload)[0] == 403
        status, created = call(
            "humanity",
            "POST",
            "/nguoi-dung/",
            user_payload,
            internal=True,
        )
        assert status == 201, created
        created_user_id = created["data"]["user_id"]
        assert created_user_id
        await humanity.users.delete_one({"_id": created_user_id})
        await humanity.users.insert_one(
            {
                "_id": USER_ID,
                **user_payload,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
            }
        )

        status, created_other = call(
            "humanity",
            "POST",
            "/nguoi-dung/",
            {
                "email": f"{OTHER_USER_ID}@example.com",
                "full_name": "Platform Other",
                "slug": OTHER_USER_ID,
                "role": "author",
            },
            internal=True,
        )
        assert status == 201, created_other
        other_created_id = created_other["data"]["user_id"]
        await humanity.users.delete_one({"_id": other_created_id})
        await humanity.users.insert_one(
            {
                "_id": OTHER_USER_ID,
                "email": f"{OTHER_USER_ID}@example.com",
                "full_name": "Platform Other",
                "slug": OTHER_USER_ID,
                "role": "author",
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
            }
        )

        await cache.sadd(f"user_sessions:{USER_ID}", USER_SESSION)
        await cache.sadd(f"user_sessions:{OTHER_USER_ID}", OTHER_SESSION)
        status, profile = call(
            "humanity",
            "GET",
            "/ho-so/ca-nhan",
            bearer=user_token,
        )
        assert status == 200 and profile["data"]["_id"] == USER_ID, profile
        status, profile = call(
            "humanity",
            "PUT",
            "/ho-so/ca-nhan",
            {"bio": "Hồ sơ integration hợp lệ"},
            bearer=user_token,
        )
        assert status == 200 and profile["data"]["bio"], profile
        status, public_profile = call(
            "humanity",
            "GET",
            f"/nguoi-dung/ten-mien/{USER_ID}",
        )
        assert status == 200 and "email" not in public_profile["data"], public_profile

        announcement = {
            "target_user_id": USER_ID,
            "title": "Platform Integration",
            "body": "Thông báo integration",
            "type": "system",
            "idempotency_key": f"platform-{uuid.uuid4()}",
        }
        assert call("notification", "POST", "/thong-bao/gui-di", announcement)[0] == 403
        status, first = call(
            "notification",
            "POST",
            "/thong-bao/gui-di",
            announcement,
            internal=True,
        )
        assert status == 201, first
        notification_id = first["data"]["id"]
        status, duplicate = call(
            "notification",
            "POST",
            "/thong-bao/gui-di",
            announcement,
            internal=True,
        )
        assert status == 201 and duplicate["data"]["duplicate"] is True, duplicate
        assert duplicate["data"]["id"] == notification_id
        status, inbox = call(
            "notification",
            "GET",
            "/thong-bao",
            bearer=user_token,
        )
        assert status == 200 and inbox["data"]["unread"] == 1, inbox
        assert call(
            "notification",
            "PATCH",
            f"/thong-bao/{notification_id}/doc-hieu",
            bearer=other_token,
        )[0] == 404
        assert call(
            "notification",
            "PATCH",
            f"/thong-bao/{notification_id}/doc-hieu",
            bearer=user_token,
        )[0] == 200

        await content.documents.insert_one(
            {
                "_id": DOCUMENT_ID,
                "slug": f"plat-drm-{uuid.uuid4().hex}",
                "creator_id": USER_ID,
                "title": "Platform DRM",
                "status": "published",
                "visibility": "public",
                "is_deleted": False,
            }
        )
        status, drm_settings = call(
            "drm",
            "PUT",
            f"/ban-quyen/{DOCUMENT_ID}",
            {"disable_copy": True, "hide_from_search": True},
            bearer=user_token,
        )
        assert status == 200 and drm_settings["data"]["disable_copy"] is True
        assert call(
            "drm",
            "PUT",
            f"/ban-quyen/{DOCUMENT_ID}",
            {"disable_copy": False, "hide_from_search": False},
            bearer=other_token,
        )[0] == 403

        await drm.drm_licenses.insert_one(
            {
                "_id": LICENSE_ID,
                "file_id": FILE_ID,
                "document_id": DOCUMENT_ID,
                "user_id": USER_ID,
                "aes_key": base64.b64encode(raw_key).decode("ascii"),
                "status": "ACTIVE",
                "open_count": 0,
                "created_at": datetime.now(timezone.utc),
            }
        )
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")
        status, license_token = call(
            "drm",
            "POST",
            "/drm/kiem-tra",
            {
                "file_id": FILE_ID,
                "client_public_key": public_key,
                "hardware_signature": "platform-device-a",
            },
            bearer=user_token,
        )
        assert status == 200, license_token
        decrypted = private_key.decrypt(
            base64.b64decode(license_token["encrypted_aes_key"]),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        assert decrypted == raw_key
        assert call(
            "drm",
            "POST",
            "/drm/kiem-tra",
            {
                "file_id": FILE_ID,
                "client_public_key": public_key,
                "hardware_signature": "platform-device-b",
            },
            bearer=user_token,
        )[0] == 403
        print("platform services integration passed")
    finally:
        await humanity.users.delete_many({"_id": {"$in": [USER_ID, OTHER_USER_ID]}})
        await notification.notifications.delete_many({"target_user_id": USER_ID})
        await notification.notification_settings.delete_one({"_id": USER_ID})
        await content.documents.delete_one({"_id": DOCUMENT_ID})
        await drm.drm_licenses.delete_one({"_id": LICENSE_ID})
        await drm.document_drm_settings.delete_many({"document_id": DOCUMENT_ID})
        await drm.audit_logs.delete_many({"document_id": DOCUMENT_ID})
        await cache.delete(
            f"user_sessions:{USER_ID}",
            f"user_sessions:{OTHER_USER_ID}",
        )
        async for key in cache.scan_iter(match=f"drm:*:{USER_ID}:*"):
            await cache.delete(key)
        await cache.aclose()
        mongo.close()


asyncio.run(main())
