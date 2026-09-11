import argparse
import asyncio
import json
import os
from datetime import datetime, timezone

import httpx
from motor.motor_asyncio import AsyncIOMotorClient


SOURCE_TYPE_MAP = {
    "teacher_material": "REFERENCE",
    "official_textbook": "REGULATION",
    "curriculum": "REGULATION",
    "reference": "REFERENCE",
    "api_contract": "API_SPEC",
    "other": "OTHER",
}
AUTHORITY_MAP = {
    "teacher": "PROJECT_REFERENCE",
    "official": "CONTROLLED_SOURCE",
    "supplemental": "SUPPLEMENTAL",
    "reference": "PROJECT_REFERENCE",
    "baseline": "APPROVED_SOURCE",
    "draft": "DRAFT",
}
CANONICAL_SOURCE_TYPES = {
    "SRS",
    "BRD",
    "USER_STORY",
    "ACCEPTANCE_CRITERIA",
    "BUSINESS_RULE",
    "API_SPEC",
    "UI_SPEC",
    "ARCHITECTURE",
    "MEETING_NOTE",
    "RELEASE_NOTE",
    "BUG_HISTORY",
    "TEST_ARTIFACT",
    "REGULATION",
    "REFERENCE",
    "OTHER",
}
CANONICAL_AUTHORITIES = {
    "APPROVED_SOURCE",
    "CONTROLLED_SOURCE",
    "PROJECT_REFERENCE",
    "SUPPLEMENTAL",
    "DRAFT",
    "UNVERIFIED",
}


def migrated_fields(document):
    source_type = document.get("source_type")
    authority = document.get("authority")
    values = {
        "source_type": source_type if source_type in CANONICAL_SOURCE_TYPES else SOURCE_TYPE_MAP.get(source_type, "OTHER"),
        "authority": authority if authority in CANONICAL_AUTHORITIES else AUTHORITY_MAP.get(authority, "UNVERIFIED"),
        "owner_id": document.get("owner_id") or document.get("teacher_id"),
        "module": document.get("module") or document.get("subject"),
        "component": document.get("component") or document.get("grade"),
        "product_area": document.get("product_area"),
        "release_id": document.get("release_id"),
        "external_source_id": document.get("external_source_id"),
        "approval_status": document.get("approval_status") or ("APPROVED" if authority == "baseline" else "DRAFT"),
        "approved_by": document.get("approved_by"),
        "approved_at": document.get("approved_at"),
        "source_version": str(document.get("source_version") or "1"),
        "effective_from": document.get("effective_from"),
        "tags": list(dict.fromkeys(str(item).strip() for item in document.get("tags", []) if str(item).strip())),
        "metadata_schema_version": 5,
        "metadata_migrated_at": datetime.now(timezone.utc),
        "index_status": "PENDING",
    }
    return values


def serialized_content(value):
    if isinstance(value, str):
        return value
    return json.dumps(value or {}, ensure_ascii=False, sort_keys=True, default=str)


def index_payload(document, values):
    text = serialized_content(document.get("normalized_content"))
    return {
        "artifact_type": "requirement_document",
        "artifact_id": str(document["_id"]),
        "artifact_version_id": str(document["_id"]),
        "title": str(document.get("title") or document.get("filename") or document["_id"]),
        "text": text[:50000],
        "status": str(document.get("status") or "READY"),
        "authority": values["authority"],
        "version": values["source_version"],
        "module": str(values.get("module") or ""),
        "metadata": {
            key: values.get(key)
            for key in (
                "owner_id",
                "component",
                "product_area",
                "release_id",
                "external_source_id",
                "approval_status",
                "approved_by",
                "approved_at",
                "effective_from",
                "tags",
                "source_type",
            )
        },
    }


async def reindex(client, ai_url, secret_key, document, values):
    payload = index_payload(document, values)
    if not payload["text"].strip():
        return False
    response = await client.post(
        f"{ai_url.rstrip('/')}/tri-thuc/du-an/{document['project_id']}/doi-tuong",
        headers={"X-Internal-Token": secret_key},
        json=payload,
    )
    response.raise_for_status()
    return True


async def migrate(apply_changes, skip_reindex):
    mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/veriq")
    database_name = os.environ.get("TESTING_DB_NAME", "testing")
    ai_url = os.environ.get("AI_URL", "http://localhost:8015")
    secret_key = os.environ.get("SECRET_KEY", "")
    mongo = AsyncIOMotorClient(mongo_uri, tz_aware=True)
    collection = mongo[database_name].requirement_documents
    documents = await collection.find({}).to_list(length=None)
    changed = 0
    indexed = 0
    failed = 0
    async with httpx.AsyncClient(timeout=120) as client:
        for document in documents:
            values = migrated_fields(document)
            changed += 1
            if not apply_changes:
                continue
            await collection.update_one(
                {"_id": document["_id"]},
                {
                    "$set": values,
                    "$unset": {"teacher_id": "", "subject": "", "grade": ""},
                },
            )
            if skip_reindex:
                continue
            try:
                if await reindex(client, ai_url, secret_key, document, values):
                    indexed += 1
                    await collection.update_one(
                        {"_id": document["_id"]},
                        {"$set": {"index_status": "INDEXED", "indexed_at": datetime.now(timezone.utc)}},
                    )
            except Exception:
                failed += 1
                await collection.update_one(
                    {"_id": document["_id"]},
                    {"$set": {"index_status": "FAILED", "index_error_code": "V5_REINDEX_FAILED"}},
                )
    remaining = await collection.count_documents(
        {"$or": [{"teacher_id": {"$exists": True}}, {"subject": {"$exists": True}}, {"grade": {"$exists": True}}]}
    )
    mongo.close()
    return {
        "mode": "apply" if apply_changes else "dry-run",
        "documents": len(documents),
        "mapped": changed,
        "indexed": indexed,
        "reindex_failed": failed,
        "legacy_fields_remaining": remaining if apply_changes else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--skip-reindex", action="store_true")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(migrate(args.apply, args.skip_reindex)), ensure_ascii=False))


if __name__ == "__main__":
    main()
