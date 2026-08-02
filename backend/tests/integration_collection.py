import asyncio
import json
import os
import tempfile
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import fitz
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis


BASE_URL = os.getenv("COLLECTION_TEST_URL", "http://127.0.0.1:8000")
ADMIN_ID = f"collection-admin-{uuid.uuid4()}"
READER_ID = f"collection-reader-{uuid.uuid4()}"
ADMIN_SESSION = str(uuid.uuid4())
READER_SESSION = str(uuid.uuid4())
SECRET_KEY = os.environ["SECRET_KEY"]


def token(user_id, session_id, role):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": f"{user_id}@doclib.local",
            "uid": user_id,
            "sid": session_id,
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        SECRET_KEY,
        algorithm="HS256",
    )


def call(method, path, bearer=None, body=None):
    headers = {"Content-Type": "application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


async def main():
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    cache = redis.from_url(os.environ["REDIS_URI"], decode_responses=True)
    collection = mongo[os.getenv("COLLECTION_DB_NAME", "doclib_collection")]
    content = mongo[os.getenv("CONTENT_DB_NAME", "doclib_content")]
    admin_token = token(ADMIN_ID, ADMIN_SESSION, "admin")
    reader_token = token(READER_ID, READER_SESSION, "reader")
    job_id = f"collection-job-{uuid.uuid4()}"
    source_url = f"https://integration.invalid/{uuid.uuid4()}"
    queue_name = f"collection_integration_{uuid.uuid4().hex}"
    try:
        await cache.sadd(f"user_sessions:{ADMIN_ID}", ADMIN_SESSION)
        await cache.sadd(f"user_sessions:{READER_ID}", READER_SESSION)
        assert call("GET", "/ready")[0] == 200
        assert call("GET", "/thu-thap/thong-ke", reader_token)[0] == 403
        status, before = call("GET", "/thu-thap/thong-ke", admin_token)
        assert status == 200, before
        await content.documents.insert_one(
            {
                "_id": f"collection-document-{uuid.uuid4()}",
                "title": "Collection Integration",
                "slug": f"collection-integration-{uuid.uuid4()}",
                "source_url": source_url,
                "file_url": "system/collection/integration/document.pdf",
                "creator_id": "ctan",
                "status": "published",
                "created_at": datetime.now(timezone.utc),
            }
        )
        await collection.collection_jobs.insert_one(
            {
                "_id": job_id,
                "source": "CTAN",
                "status": "pending",
                "progress": 0,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        )
        status, jobs = call("GET", "/thu-thap/tien-trinh-dang-chay", admin_token)
        assert status == 200 and any(job["id"] == job_id for job in jobs), jobs
        status, after = call("GET", "/thu-thap/thong-ke", admin_token)
        assert status == 200, after
        assert after["total_documents"] >= before["total_documents"] + 1
        assert after["total_documents_collected"] >= before["total_documents_collected"] + 1
        assert after["active_jobs"] >= 1

        from src.core.database import database as document_database
        from src.core.infrastructure.database import database as infrastructure
        from src.core.infrastructure.mq import mq

        infrastructure.mongodb = mongo
        from src.services import metadata as metadata_service

        class MetadataStorage:
            async def upload_local_file(
                self,
                object_name,
                local_file_path,
                content_type="application/pdf",
            ):
                assert os.path.getsize(local_file_path) > 0
                return object_name

        metadata_service.storage = MetadataStorage()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as stream:
            pdf_path = stream.name
        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_text((72, 72), "DocLib")
        pdf.save(pdf_path)
        pdf.close()
        metadata = await metadata_service.anna_metadata(
            {
                "title": "Collected document",
                "author": "Collected author",
                "source_url": source_url,
            },
            pdf_path,
            "system/collection/integration/metadata.pdf",
            "pdf",
        )
        os.unlink(pdf_path)
        assert metadata["description"] == ""
        assert metadata["publisher_name"] == "DocLib"
        assert metadata["visibility"] == "private"
        assert metadata["status"] == "draft"
        assert metadata["collection_status"] == "ready_for_review"
        assert metadata["pages_count"] == 1
        assert metadata["cover_url"].endswith("cover.png")
        first_id = await document_database.insert_document(
            {
                "title": "Idempotent Integration",
                "slug": f"idempotent-integration-{uuid.uuid4()}",
                "source_url": source_url,
                "file_url": "system/collection/integration/idempotent.pdf",
                "creator_id": "ctan",
                "status": "published",
            }
        )
        second_id = await document_database.insert_document(
            {
                "title": "Duplicate Integration",
                "slug": f"duplicate-integration-{uuid.uuid4()}",
                "source_url": source_url,
                "file_url": "system/collection/integration/duplicate.pdf",
                "creator_id": "ctan",
                "status": "published",
            }
        )
        assert first_id == second_id
        assert await content.documents.count_documents({"source_url": source_url}) == 1
        queue = await mq.get_queue(queue_name)
        await mq.publish(queue_name, {"kind": "integration", "value": 1})
        message = await mq.consume(queue_name, timeout=5)
        assert message["payload"]["kind"] == "integration"
        assert await mq.ack(message["delivery_tag"])
        await queue.delete(if_unused=False, if_empty=False)
        assert call("GET", "/thu-thap/nhat-ky", admin_token)[0] == 200
        print("collection integration passed")
    finally:
        await collection.collection_jobs.delete_many({"_id": job_id})
        await content.documents.delete_many({"source_url": source_url})
        await cache.delete(f"user_sessions:{ADMIN_ID}", f"user_sessions:{READER_ID}")
        await cache.aclose()
        mongo.close()


asyncio.run(main())
