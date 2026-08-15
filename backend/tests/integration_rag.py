import json
import os
import urllib.error
import urllib.request
import uuid

import boto3
from pymongo import MongoClient


SECRET_KEY = os.environ["SECRET_KEY"]
USER_ID = f"rag-user-{uuid.uuid4()}"
OTHER_USER_ID = f"rag-other-{uuid.uuid4()}"
DOCUMENT_ID = f"rag-document-{uuid.uuid4()}"
OBJECT_KEY = f"integration/rag/{uuid.uuid4()}.txt"
HTTP_TIMEOUT = float(os.getenv("INTEGRATION_HTTP_TIMEOUT_SECONDS", "900"))


def call(method: str, path: str, body=None, internal: bool = True):
    headers = {"Content-Type": "application/json"}
    if internal:
        headers["X-Internal-Token"] = SECRET_KEY
    request = urllib.request.Request(
        f"http://rag:8000{path}",
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            payload = response.read()
            return response.status, json.loads(payload) if payload else None
    except urllib.error.HTTPError as error:
        payload = error.read()
        return error.code, json.loads(payload) if payload else None


def main():
    mongo = MongoClient(os.environ["MONGODB_URI"])
    content = mongo[os.getenv("CONTENT_DB_NAME", "doclib_content")]
    storage = boto3.client(
        "s3",
        endpoint_url=os.environ["MINIO_ENDPOINT"],
        aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
        aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
        region_name=os.environ["MINIO_REGION"],
    )
    bucket = os.environ["MINIO_PRIVATE_BUCKET"]
    text = (
        "DocLib retrieval integration verifies private document indexing ownership "
        "semantic retrieval cache vector storage and cleanup across service boundaries"
    )
    try:
        storage.put_object(Bucket=bucket, Key=OBJECT_KEY, Body=text.encode("utf-8"))
        content.documents.insert_one(
            {
                "_id": DOCUMENT_ID,
                "slug": DOCUMENT_ID,
                "title": "RAG Integration",
                "author": "DocLib",
                "creator_id": USER_ID,
                "file_url": OBJECT_KEY,
                "content_format": "txt",
                "visibility": "private",
                "status": "published",
                "is_deleted": False,
            }
        )

        status, readiness = call("GET", "/ready", internal=False)
        assert status == 200 and readiness["status"] == "ready", readiness

        status, protected = call(
            "POST",
            "/rag/embedding/query",
            {"text": "protected"},
            internal=False,
        )
        assert status == 403, protected

        status, embedded = call(
            "POST",
            "/rag/embedding/query",
            {"text": "DocLib integration embedding"},
        )
        vector = embedded["data"]["embedding"]
        assert status == 200 and len(vector) == 1024 and any(vector), embedded

        status, denied = call(
            "POST",
            "/rag/ingest",
            {
                "document_id": DOCUMENT_ID,
                "requester_id": OTHER_USER_ID,
                "is_admin": False,
            },
        )
        assert status == 403, denied

        status, ingested = call(
            "POST",
            "/rag/ingest",
            {
                "document_id": DOCUMENT_ID,
                "requester_id": USER_ID,
                "is_admin": False,
            },
        )
        assert status == 200 and ingested["data"]["chunks_count"] > 0, ingested

        indexed = content.documents.find_one({"_id": DOCUMENT_ID})
        assert indexed["is_indexed"] is True and indexed["chunks_count"] > 0

        status, hidden = call(
            "POST",
            "/rag/retrieve",
            {
                "query": "private document indexing ownership",
                "document_ids": [DOCUMENT_ID],
                "k": 3,
                "requester_id": OTHER_USER_ID,
                "is_admin": False,
            },
        )
        assert status == 200 and hidden["data"]["documents"] == [], hidden

        status, retrieved = call(
            "POST",
            "/rag/retrieve",
            {
                "query": "private document indexing ownership",
                "document_ids": [DOCUMENT_ID],
                "k": 3,
                "requester_id": USER_ID,
                "is_admin": False,
            },
        )
        assert status == 200 and retrieved["data"]["documents"], retrieved
        assert retrieved["data"]["documents"][0]["metadata"]["document_id"] == DOCUMENT_ID

        status, multi_query = call(
            "POST",
            "/rag/multi-query-retrieve",
            {
                "question": "How does private document indexing preserve ownership",
                "document_ids": [DOCUMENT_ID],
                "k": 5,
                "requester_id": USER_ID,
                "is_admin": False,
            },
        )
        assert status == 200 and multi_query["data"]["documents"], multi_query
        assert any(
            document["metadata"].get("document_id") == DOCUMENT_ID
            for document in multi_query["data"]["documents"]
        ), multi_query

        status, extracted = call(
            "POST",
            "/rag/extract",
            {
                "document_id": DOCUMENT_ID,
                "requester_id": USER_ID,
                "is_admin": False,
            },
        )
        assert status == 200 and "service boundaries" in extracted["data"]["text"]

        status, stored = call(
            "POST",
            "/rag/cache/set",
            {
                "query_text": "rag integration cache",
                "response_text": "cache verified",
                "query_vector": vector,
            },
        )
        assert status == 200, stored
        status, cached = call(
            "POST",
            "/rag/cache/get",
            {"query_text": "rag integration cache", "query_vector": vector},
        )
        assert status == 200 and cached["data"]["hit"] is True, cached

        status, deleted = call(
            "DELETE",
            f"/rag/document/{DOCUMENT_ID}?requester_id={USER_ID}&is_admin=false",
        )
        assert status == 200 and deleted["data"]["status"] == "deleted", deleted

        unindexed = content.documents.find_one({"_id": DOCUMENT_ID})
        assert unindexed["is_indexed"] is False and unindexed["chunks_count"] == 0

        status, empty = call(
            "POST",
            "/rag/retrieve",
            {
                "query": "private document indexing ownership",
                "document_ids": [DOCUMENT_ID],
                "k": 3,
                "requester_id": USER_ID,
                "is_admin": False,
            },
        )
        assert status == 200 and empty["data"]["documents"] == [], empty
        print("rag_integration_passed")
    finally:
        try:
            call(
                "DELETE",
                f"/rag/document/{DOCUMENT_ID}?requester_id={USER_ID}&is_admin=true",
            )
        except Exception:
            pass
        content.documents.delete_one({"_id": DOCUMENT_ID})
        try:
            storage.delete_object(Bucket=bucket, Key=OBJECT_KEY)
        except Exception:
            pass
        mongo.close()


if __name__ == "__main__":
    main()
