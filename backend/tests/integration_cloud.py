import asyncio
import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import aioboto3
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis


BASE_URL = os.getenv("CLOUD_TEST_URL", "http://traefik:8000")
OWNER_ID = f"cloud-owner-{uuid.uuid4()}"
SHARED_ID = f"cloud-shared-{uuid.uuid4()}"
OWNER_SESSION = str(uuid.uuid4())
SHARED_SESSION = str(uuid.uuid4())
SECRET_KEY = os.getenv("SECRET_KEY", "doclib-password")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def token(user_id, session_id, role="reader", ai_tier="BASIC"):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": f"{user_id}@doclib.local",
            "uid": user_id,
            "sid": session_id,
            "role": role,
            "ai_tier": ai_tier,
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        SECRET_KEY,
        algorithm="HS256",
    )


def call(method, path, bearer=None, body=None, raw=None, headers=None, follow=True):
    request_headers = dict(headers or {})
    if bearer:
        request_headers["Authorization"] = f"Bearer {bearer}"
    if body is not None:
        request_headers["Content-Type"] = "application/json"
        raw = json.dumps(body).encode()
    request = urllib.request.Request(f"{BASE_URL}{path}", data=raw, headers=request_headers, method=method)
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(request, timeout=20) as response:
            content = response.read()
            if not content:
                payload = None
            try:
                payload = json.loads(content) if content else None
            except json.JSONDecodeError:
                payload = content
            return response.status, payload, response.headers
    except urllib.error.HTTPError as error:
        content = error.read()
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            payload = content.decode(errors="ignore")
        return error.code, payload, error.headers


def multipart(filename, content, content_type="text/plain"):
    boundary = f"doclib-{uuid.uuid4().hex}"
    data = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    return data, {"Content-Type": f"multipart/form-data; boundary={boundary}"}


async def main():
    mongo = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/doclib"))
    cache = redis.from_url(os.getenv("REDIS_URI", "redis://127.0.0.1:6379/0"), decode_responses=True)
    cloud = mongo[os.getenv("CLOUD_DB_NAME", "doclib_cloud")]
    humanity = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    owner_token = token(OWNER_ID, OWNER_SESSION, ai_tier="PRO")
    shared_token = token(SHARED_ID, SHARED_SESSION, ai_tier="PRO")
    object_paths = []
    try:
        await cache.sadd(f"user_sessions:{OWNER_ID}", OWNER_SESSION)
        await cache.sadd(f"user_sessions:{SHARED_ID}", SHARED_SESSION)
        await humanity.users.insert_many([
            {"_id": OWNER_ID, "email": f"{OWNER_ID}@doclib.local", "role": "reader", "storage_limit": 20 * 1024 * 1024},
            {"_id": SHARED_ID, "email": f"{SHARED_ID}@doclib.local", "role": "reader", "storage_limit": 20 * 1024 * 1024},
        ])
        assert call("GET", "/ready")[0] == 200
        content = b"cloud-integration-data" * 300
        data, headers = multipart("integration.txt", content)
        status, payload, _ = call("POST", "/tai-len/tap-tin", owner_token, raw=data, headers=headers)
        assert status == 200 or status == 201, payload
        item_id = payload["data"]["item_id"]
        path = payload["data"]["url"]
        object_paths.append(path)
        assert path.startswith(f"users/{OWNER_ID}/")
        assert await cloud.storage_items.find_one({"_id": item_id, "size": len(content)})
        status, search_results, _ = call(
            "GET",
            "/tim-kiem/luu-tru?q=integration&extension=txt",
            owner_token,
        )
        assert status == 200, search_results
        assert any(item["_id"] == item_id for item in search_results["data"])
        status, preview, _ = call(
            "GET",
            f"/tim-kiem/xem-truoc/{item_id}",
            owner_token,
        )
        assert status == 200, preview
        assert preview["data"]["preview_type"] == "text"
        assert preview["data"]["stream_url"].startswith("http")
        status, download, _ = call(
            "GET",
            f"/tai-ve/{item_id}/duong-dan",
            owner_token,
        )
        assert status == 200, download
        assert download["data"]["download_url"].startswith("http")
        media_item_ids = []
        media_content = b"editor-media" * 500
        for filename, content_type, expected_folder in (
            ("editor.mp4", "video/mp4", "videos"),
            ("editor.mp3", "audio/mpeg", "audio"),
        ):
            media_data, media_headers = multipart(filename, media_content, content_type)
            status, media_payload, _ = call(
                "POST",
                "/tai-len/tap-tin",
                owner_token,
                raw=media_data,
                headers=media_headers,
            )
            assert status == 201, media_payload
            media_path = media_payload["data"]["url"]
            assert media_path.startswith(f"users/{OWNER_ID}/{expected_folder}/")
            assert call("GET", f"/tai-len/noi-dung/{media_path}", owner_token)[0] == 200
            media_item_ids.append(media_payload["data"]["item_id"])
        invalid_media, invalid_media_headers = multipart(
            "invalid.mp4",
            b"invalid-media" * 500,
            "text/plain",
        )
        assert call(
            "POST",
            "/tai-len/tap-tin",
            owner_token,
            raw=invalid_media,
            headers=invalid_media_headers,
        )[0] == 400
        status, quota, _ = call("GET", "/luu-tru/han-muc", owner_token)
        assert status == 200
        assert quota["data"]["used"] == len(content) + 2 * len(media_content), quota
        assert call("GET", f"/tai-len/luu-tru/{path}", shared_token, follow=False)[0] == 403
        version_content = b"cloud-version-data" * 400
        version_data, version_headers = multipart(
            "integration-version.txt",
            version_content,
        )
        status, uploaded_version, _ = call(
            "POST",
            "/tai-len/tap-tin",
            owner_token,
            raw=version_data,
            headers=version_headers,
        )
        assert status in {200, 201}, uploaded_version
        staged_version_id = uploaded_version["data"]["item_id"]
        version_path = uploaded_version["data"]["url"]
        object_paths.append(version_path)
        status, versioned_item, _ = call(
            "POST",
            f"/luu-tru/tap-tin/{item_id}/phien-ban",
            owner_token,
            {"url": version_path, "size": len(version_content)},
        )
        assert status == 200, versioned_item
        assert await cloud.storage_items.find_one({"_id": staged_version_id}) is None
        status, versions, _ = call(
            "GET",
            f"/luu-tru/phien-ban/{item_id}",
            owner_token,
        )
        assert status == 200 and len(versions["data"]) == 1, versions
        old_version_id = versions["data"][0]["version_id"]
        assert versions["data"][0]["url"] == path
        status, restored, _ = call(
            "POST",
            f"/luu-tru/phien-ban/{item_id}/khoi-phuc/{old_version_id}",
            owner_token,
        )
        assert status == 200, restored
        current_item = await cloud.storage_items.find_one({"_id": item_id})
        assert current_item["url"] == path
        status, quota, _ = call("GET", "/luu-tru/han-muc", owner_token)
        assert status == 200
        assert quota["data"]["used"] == len(content) + len(version_content) + 2 * len(media_content), quota

        status, share_payload, _ = call(
            "POST",
            f"/luu-tru/tap-tin/{item_id}/chia-se",
            owner_token,
            {"email": f"{SHARED_ID}@doclib.local", "role": "viewer"},
        )
        assert status == 200, share_payload
        assert call("GET", f"/tai-len/luu-tru/{path}", shared_token, follow=False)[0] == 302
        status, public_payload, _ = call("PUT", f"/luu-tru/tap-tin/{item_id}", owner_token, {"is_public": True})
        assert status == 200, public_payload
        share_token = public_payload["data"]["share_token"]
        status, public_item, _ = call("GET", f"/luu-tru/chia-se/{share_token}")
        assert status == 200 and public_item["data"]["download_url"], public_item
        protected_status, protected_link, _ = call(
            "POST",
            "/luu-tru/link-chia-se/tao",
            owner_token,
            {
                "item_id": item_id,
                "password": "ProtectedShare123",
                "expires_in_hours": 24,
            },
        )
        assert protected_status == 201, protected_link
        protected_token = protected_link["data"]["share_token"]
        assert call(
            "GET",
            f"/luu-tru/link-chia-se/xac-thuc/{protected_token}?password=invalid",
        )[0] == 403
        assert call(
            "GET",
            f"/luu-tru/link-chia-se/xac-thuc/{protected_token}?password=ProtectedShare123",
        )[0] == 200
        expired_token = f"expired-{uuid.uuid4()}"
        await cloud.storage_share_links.insert_one(
            {
                "_id": expired_token,
                "item_id": item_id,
                "owner_id": OWNER_ID,
                "has_password": False,
                "created_at": datetime.now(timezone.utc) - timedelta(hours=2),
                "expires_at": datetime.now(timezone.utc) - timedelta(hours=1),
            }
        )
        assert call(
            "GET",
            f"/luu-tru/link-chia-se/xac-thuc/{expired_token}",
        )[0] == 410

        reserved_content = b"presigned-cloud-data" * 300
        request_body = {"filename": "presigned.txt", "size": len(reserved_content), "content_type": "text/plain"}
        status, reserved, _ = call("POST", "/tai-len/presigned-url", owner_token, request_body)
        assert status == 200, reserved
        reserved_path = reserved["data"]["file_path"]
        object_paths.append(reserved_path)
        async with aioboto3.Session().client(
            "s3",
            endpoint_url=os.environ["MINIO_ENDPOINT"],
            aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
            aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
        ) as storage:
            await storage.put_object(
                Bucket=os.environ["MINIO_PRIVATE_BUCKET"],
                Key=reserved_path,
                Body=reserved_content,
                ContentType="text/plain",
            )
        confirm = {**request_body, "file_path": reserved_path}
        status, confirmed, _ = call("POST", "/tai-len/xac-nhan", owner_token, confirm)
        assert status == 201, confirmed
        confirmed_item_id = confirmed["data"]["item_id"]
        assert call("POST", "/tai-len/xac-nhan", owner_token, confirm)[0] == 409
        assert call("POST", "/tai-len/xac-nhan", owner_token, {**confirm, "file_path": f"users/{OWNER_ID}/documents/forged.txt"})[0] == 409

        status, folder_payload, _ = call("POST", "/luu-tru/thu-muc", owner_token, {"name": "parent"})
        assert status == 201, folder_payload
        folder_id = folder_payload["data"]["_id"]
        status, child_payload, _ = call("POST", "/luu-tru/thu-muc", owner_token, {"name": "child", "parent_id": folder_id})
        assert status == 201, child_payload
        child_id = child_payload["data"]["_id"]
        assert call("PUT", f"/luu-tru/tap-tin/{folder_id}", owner_token, {"parent_id": child_id})[0] == 404
        assert call(
            "PATCH",
            f"/thu-muc/{folder_id}/di-chuyen",
            owner_token,
            {"parent_id": child_id},
        )[0] == 400
        assert call("DELETE", f"/luu-tru/tap-tin/{folder_id}", owner_token)[0] == 200
        child = await cloud.storage_items.find_one({"_id": child_id})
        assert child["is_trashed"] is True
        assert call("DELETE", f"/luu-tru/tap-tin/{folder_id}?hard_delete=true", owner_token)[0] == 200
        assert await cloud.storage_items.find_one({"_id": child_id}) is None
        assert call("DELETE", f"/luu-tru/tap-tin/{item_id}?hard_delete=true", owner_token)[0] == 200
        assert call("DELETE", f"/luu-tru/tap-tin/{confirmed_item_id}?hard_delete=true", owner_token)[0] == 200
        for media_item_id in media_item_ids:
            assert call("DELETE", f"/luu-tru/tap-tin/{media_item_id}?hard_delete=true", owner_token)[0] == 200
        print("cloud integration passed")
    finally:
        records = await cloud.storage_items.find({"owner_id": {"$in": [OWNER_ID, SHARED_ID]}}).to_list(length=None)
        object_paths.extend(record.get("url") for record in records if record.get("url"))
        await cloud.storage_items.delete_many({"owner_id": {"$in": [OWNER_ID, SHARED_ID]}})
        await cloud.temp_chat_files.delete_many({"owner_id": {"$in": [OWNER_ID, SHARED_ID]}})
        await cloud.storage_share_links.delete_many({"owner_id": {"$in": [OWNER_ID, SHARED_ID]}})
        await humanity.users.delete_many({"_id": {"$in": [OWNER_ID, SHARED_ID]}})
        await cache.delete(f"user_sessions:{OWNER_ID}", f"user_sessions:{SHARED_ID}")
        async for key in cache.scan_iter(match="cloud:upload:*"):
            value = await cache.get(key)
            if value and json.loads(value).get("owner_id") in {OWNER_ID, SHARED_ID}:
                await cache.delete(key)
        await cache.aclose()
        mongo.close()


asyncio.run(main())
