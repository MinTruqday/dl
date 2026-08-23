import asyncio
import os
from uuid import uuid4

import boto3
import httpx


async def content_request(client, secret, payload):
    response = await client.post(
        "http://content:8000/tai-lieu/noi-bo/tai-lieu",
        headers={"X-Internal-Token": secret},
        json=payload,
    )
    response.raise_for_status()
    return response.json().get("data")


async def main():
    secret = os.environ["SECRET_KEY"]
    run_id = uuid4().hex
    document_id = f"TMR-{run_id}"
    owner_id = f"teacher-a-{run_id}"
    other_owner_id = f"teacher-b-{run_id}"
    object_key = f"system/documents/{document_id}.md"
    unique_term = f"teacher isolated {run_id[:8]} {run_id[8:16]}"
    body = (
        f"# Chuyên đề riêng\n\n{unique_term} là ký hiệu dùng trong chuyên đề đạo hàm riêng của giáo viên "
        "Nội dung này chỉ được dùng làm nguồn bổ trợ và không thay thế chương trình chính thống\n"
    ).encode()
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["MINIO_ENDPOINT"],
        aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
        aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
        region_name="us-east-1",
    )
    bucket = os.environ["MINIO_PRIVATE_BUCKET"]
    s3.put_object(Bucket=bucket, Key=object_key, Body=body, ContentType="text/markdown")
    headers = {"X-Internal-Token": secret}
    async with httpx.AsyncClient(timeout=180) as client:
        await content_request(
            client,
            secret,
            {
                "operation": "update_one",
                "query": {"_id": document_id},
                "update": {
                    "$set": {
                        "_id": document_id,
                        "title": "Chuyên đề riêng",
                        "slug": f"chuyen-de-rieng-{run_id}",
                        "creator_id": owner_id,
                        "visibility": "private",
                        "file_url": object_key,
                        "content_format": "markdown",
                        "is_deleted": False,
                        "education_metadata": {
                            "source_type": "teacher_material",
                            "authority": "supplementary",
                            "education_level": "THPT",
                            "subject": "math",
                            "target_program": "grade_12",
                            "concept_ids": ["derivative"],
                            "skill_ids": ["differentiate"],
                            "source_version": run_id,
                            "mapping_status": "confirmed",
                            "mapping_confidence": 1,
                        },
                    }
                },
                "upsert": True,
            },
        )
        ingest = await client.post(
            "http://127.0.0.1:8000/rag/ingest",
            headers=headers,
            json={"document_id": document_id, "requester_id": owner_id, "is_admin": False},
        )
        ingest.raise_for_status()
        if ingest.json()["data"]["status"] != "indexed":
            raise AssertionError("Teacher material was not indexed")
        stored = await content_request(
            client, secret, {"operation": "find_one", "query": {"_id": document_id}}
        )
        if stored.get("indexing_status") != "indexed" or stored.get("is_indexed") is not True:
            raise AssertionError("Content indexing status was not synchronized")
        retrieve_payload = {
            "query": unique_term,
            "k": 10,
            "metadata_filters": {
                "source_type": "teacher_material",
                "subject": "math",
                "target_program": "grade_12",
            },
        }
        owner_response = await client.post(
            "http://127.0.0.1:8000/rag/retrieve",
            headers=headers,
            json={**retrieve_payload, "requester_id": owner_id},
        )
        owner_response.raise_for_status()
        owner_documents = owner_response.json()["data"]["documents"]
        if document_id not in {row["metadata"].get("document_id") for row in owner_documents}:
            raise AssertionError("Owner could not retrieve the indexed teacher material")
        other_response = await client.post(
            "http://127.0.0.1:8000/rag/retrieve",
            headers=headers,
            json={**retrieve_payload, "requester_id": other_owner_id},
        )
        other_response.raise_for_status()
        other_documents = other_response.json()["data"]["documents"]
        if document_id in {row["metadata"].get("document_id") for row in other_documents}:
            raise AssertionError("Teacher material crossed owner isolation")
        audit_response = await client.get(
            "http://127.0.0.1:8000/rag/audit/material-access",
            headers=headers,
            params={"requester_id": owner_id, "document_id": document_id},
        )
        audit_response.raise_for_status()
        audit_rows = audit_response.json()
        if not any(
            row.get("requester_id") == owner_id
            and document_id in row.get("document_ids", [])
            and row.get("query_sha256")
            and "query" not in row
            for row in audit_rows
        ):
            raise AssertionError("Teacher material access was not audited safely")
        proxy_owner_response = await client.get(
            "http://assessment:8000/teacher-materials/search",
            headers={"X-Test-User-Id": owner_id, "X-Test-User-Role": "author"},
            params={"q": unique_term, "subject": "math"},
        )
        proxy_owner_response.raise_for_status()
        if document_id not in {
            row["metadata"].get("document_id")
            for row in proxy_owner_response.json().get("documents", [])
        }:
            raise AssertionError(
                "Assessment teacher material search did not return the owner document"
            )
        proxy_other_response = await client.get(
            "http://assessment:8000/teacher-materials/search",
            headers={"X-Test-User-Id": other_owner_id, "X-Test-User-Role": "author"},
            params={"q": unique_term, "subject": "math"},
        )
        proxy_other_response.raise_for_status()
        if document_id in {
            row["metadata"].get("document_id")
            for row in proxy_other_response.json().get("documents", [])
        }:
            raise AssertionError("Assessment teacher material search crossed owner isolation")
        deleted = await client.delete(
            f"http://127.0.0.1:8000/rag/document/{document_id}",
            headers=headers,
            params={"requester_id": owner_id},
        )
        deleted.raise_for_status()
        await content_request(
            client,
            secret,
            {
                "operation": "update_one",
                "query": {"_id": document_id},
                "update": {"$set": {"is_deleted": True}},
            },
        )
        metrics_response = await client.get("http://127.0.0.1:8000/metrics")
        metrics_response.raise_for_status()
        if "rag_curriculum_retrieval_hit_rate" not in metrics_response.text:
            raise AssertionError("RAG curriculum retrieval metric is unavailable")
    s3.delete_object(Bucket=bucket, Key=object_key)
    print("teacher material content to rag integration passed")


if __name__ == "__main__":
    asyncio.run(main())
