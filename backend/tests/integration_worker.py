import asyncio
import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

import aioboto3
from motor.motor_asyncio import AsyncIOMotorClient


BASE_URL = os.getenv("WORKER_TEST_URL", "http://127.0.0.1:8000")
SECRET_KEY = os.environ["SECRET_KEY"]
CREATOR_ID = f"worker-creator-{uuid.uuid4()}"
DOCUMENT_ID = f"worker-document-{uuid.uuid4()}"
UNSAFE_DOCUMENT_ID = f"worker-unsafe-{uuid.uuid4()}"
SCHEDULED_DOCUMENT_ID = f"worker-scheduled-{uuid.uuid4()}"


def call(method, path, body=None, internal=False):
    headers = {"Content-Type": "application/json"}
    if internal:
        headers["X-Internal-Token"] = SECRET_KEY
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


async def wait_for_job(worker_jobs, job_id, expected, timeout=45):
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        job = await worker_jobs.find_one({"_id": job_id})
        if job and job.get("status") == expected:
            return job
        if job and job.get("status") in {"failed", "completed"}:
            raise AssertionError(job)
        await asyncio.sleep(0.5)
    raise AssertionError(f"Job {job_id} did not reach {expected}")


async def wait_for_document(documents, document_id, expected, timeout=30):
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        document = await documents.find_one({"_id": document_id})
        if document and document.get("status") == expected:
            return document
        await asyncio.sleep(0.5)
    raise AssertionError(f"Document {document_id} did not reach {expected}")


async def main():
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    content = mongo[os.getenv("CONTENT_DB_NAME", "doclib_content")]
    worker = mongo[os.getenv("WORKER_DB_NAME", "doclib_worker")]
    storage_session = aioboto3.Session()
    object_paths = []
    now = datetime.now(timezone.utc)
    try:
        await content.documents.insert_many(
            [
                {
                    "_id": DOCUMENT_ID,
                    "slug": f"worker-integration-{uuid.uuid4()}",
                    "title": "Worker Integration",
                    "creator_id": CREATOR_ID,
                    "status": "draft",
                    "visibility": "private",
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "_id": UNSAFE_DOCUMENT_ID,
                    "slug": f"worker-unsafe-{uuid.uuid4()}",
                    "title": "Worker Unsafe",
                    "creator_id": CREATOR_ID,
                    "status": "draft",
                    "visibility": "private",
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "_id": SCHEDULED_DOCUMENT_ID,
                    "slug": f"worker-scheduled-{uuid.uuid4()}",
                    "title": "Worker Scheduled",
                    "creator_id": CREATOR_ID,
                    "status": "draft",
                    "visibility": "private",
                    "scheduled_publish_at": now - timedelta(minutes=1),
                    "created_at": now,
                    "updated_at": now,
                },
            ]
        )
        assert call("GET", "/ready")[0] == 200
        assert call(
            "POST",
            "/worker/internal/documents/compile",
            {
                "document_id": DOCUMENT_ID,
                "creator_id": CREATOR_ID,
                "tex_content": "\\documentclass{article}\\begin{document}Worker integration\\end{document}",
            },
        )[0] == 403
        status, queued = call(
            "POST",
            "/worker/internal/documents/compile",
            {
                "document_id": DOCUMENT_ID,
                "creator_id": CREATOR_ID,
                "tex_content": "\\documentclass{article}\\begin{document}Worker integration\\end{document}",
            },
            internal=True,
        )
        assert status == 200 and queued["status"] == "queued", queued
        completed = await wait_for_job(worker.worker_jobs, queued["job_id"], "completed")
        assert completed["result"]["size"] > 100
        object_path = completed["result"]["file_url"]
        object_paths.append(object_path)
        document = await content.documents.find_one({"_id": DOCUMENT_ID})
        assert document["compiled_file_url"] == object_path
        assert document["compile_status"] == "completed"
        status, fetched = call(
            "GET",
            f"/worker/internal/jobs/{queued['job_id']}",
            internal=True,
        )
        assert status == 200 and fetched["status"] == "completed"

        status, unsafe = call(
            "POST",
            "/worker/internal/documents/compile",
            {
                "document_id": UNSAFE_DOCUMENT_ID,
                "creator_id": CREATOR_ID,
                "tex_content": "\\input{/etc/passwd}",
            },
            internal=True,
        )
        assert status == 200, unsafe
        failed = await wait_for_job(worker.worker_jobs, unsafe["job_id"], "failed")
        assert failed["error"]
        unsafe_document = await content.documents.find_one({"_id": UNSAFE_DOCUMENT_ID})
        assert unsafe_document["compile_status"] == "failed"

        scheduled = await wait_for_document(
            content.documents,
            SCHEDULED_DOCUMENT_ID,
            "published",
            timeout=35,
        )
        assert scheduled["published_at"]
        assert "scheduled_publish_at" not in scheduled

        async with storage_session.client(
            "s3",
            endpoint_url=os.environ["MINIO_ENDPOINT"],
            aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
            aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
        ) as storage:
            response = await storage.get_object(
                Bucket=os.getenv("MINIO_PRIVATE_BUCKET", "doclib-private"),
                Key=object_path,
            )
            pdf = await response["Body"].read()
            assert pdf.startswith(b"%PDF")
        print("worker integration passed")
    finally:
        async with storage_session.client(
            "s3",
            endpoint_url=os.environ["MINIO_ENDPOINT"],
            aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
            aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
        ) as storage:
            for object_path in object_paths:
                await storage.delete_object(
                    Bucket=os.getenv("MINIO_PRIVATE_BUCKET", "doclib-private"),
                    Key=object_path,
                )
        await content.documents.delete_many(
            {
                "_id": {
                    "$in": [
                        DOCUMENT_ID,
                        UNSAFE_DOCUMENT_ID,
                        SCHEDULED_DOCUMENT_ID,
                    ]
                }
            }
        )
        await worker.worker_jobs.delete_many(
            {
                "document_id": {
                    "$in": [
                        DOCUMENT_ID,
                        UNSAFE_DOCUMENT_ID,
                        SCHEDULED_DOCUMENT_ID,
                    ]
                }
            }
        )
        mongo.close()


asyncio.run(main())
