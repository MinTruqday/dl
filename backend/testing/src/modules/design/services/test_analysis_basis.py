import re
from functools import lru_cache

from fastapi import HTTPException
from pymongo import MongoClient

from src.core.common import get_project
from src.core.configuration import settings
from src.repositories.requirement_analysis import requirement_analysis_repository
from src.modules.quality.services.quality_policy import evaluate_rules

@lru_cache(maxsize=1)
def basis_collections():
    client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        document = client[settings.TESTING_DB_NAME].runtime_policies.find_one(
            {"_id": "test_analysis_basis"}, {"_id": 0, "values": 1}
        )
    finally:
        client.close()
    values = document.get("values") if isinstance(document, dict) else None
    collections = values.get("collections") if isinstance(values, dict) else None
    if not isinstance(collections, dict):
        raise RuntimeError("Thiếu chính sách cơ sở phân tích kiểm thử")
    return collections





def basis_text(value):
    for field in ['plain_text_projection', 'plain_text', 'normalized_content', 'description', 'title', 'name']:
        if value.get(field):
            return str(value[field])[: int(4000)]
    return ""


async def resolve_basis(project_id, refs):
    snapshots = []
    seen = set()
    for ref in refs:
        key = (ref.artifact_type, ref.artifact_id, ref.artifact_version_id)
        if key in seen:
            raise HTTPException(status_code=422, detail={"code": 'DUPLICATE_TEST_BASIS_REF'})
        seen.add(key)
        collection = basis_collections()[ref.artifact_type]
        identifier = ref.artifact_version_id or ref.artifact_id
        query = {"_id": identifier, "project_id": project_id}
        if ref.artifact_type == 'REGULATION':
            query["source_type"] = 'REGULATION'
        value = await requirement_analysis_repository.find_basis(collection, query)
        if not value:
            global_query = {"_id": identifier}
            if ref.artifact_type == 'REGULATION':
                global_query["source_type"] = 'REGULATION'
            exists = await requirement_analysis_repository.find_basis(
                collection, global_query, {"_id": 1}
            )
            code = (
                'TEST_BASIS_PROJECT_MISMATCH'
                if exists
                else 'TEST_BASIS_NOT_FOUND'
            )
            raise HTTPException(
                status_code=422,
                detail={
                    "code": code,
                    "artifact_type": ref.artifact_type,
                    "artifact_id": identifier,
                },
            )
        text = basis_text(value)
        if ref.artifact_type == 'REQUIREMENT_VERSION':
            criteria = await requirement_analysis_repository.list_acceptance_criteria(
                {"requirement_version_id": identifier, "project_id": project_id},
                limit=200,
            )
            parts = [text]
            parts.extend(
                str(item.get("plain_text") or "").strip()
                for item in criteria
                if str(item.get("plain_text") or "").strip()
            )
            parts.extend(
                str(item).strip() for item in value.get("business_rules", []) if str(item).strip()
            )
            text = "\n".join(part for part in parts if part)
        snapshots.append(
            {
                **ref.model_dump(),
                "resolved_id": identifier,
                "title": value.get("title")
                or value.get("name")
                or value.get("filename")
                or identifier,
                "status": value.get("status"),
                "source_hash": value.get("normalized_content_hash") or value.get("content_hash"),
                "text": text,
            }
        )
    return snapshots


async def list_test_basis(project_id, user, artifact_type="", query_text="", limit=200):
    await get_project(project_id, user, "testanalysis.read")
    collections = basis_collections()
    types = [artifact_type] if artifact_type else list(collections)
    items = []
    for kind in types:
        collection_name = collections.get(kind)
        if not collection_name:
            raise HTTPException(status_code=422, detail={"code": 'TEST_BASIS_TYPE_INVALID'})
        query = {"project_id": project_id}
        if query_text:
            pattern = {"$regex": re.escape(query_text), "$options": "i"}
            query["$or"] = [
                {"title": pattern},
                {"name": pattern},
                {"plain_text_projection": pattern},
            ]
        values = await requirement_analysis_repository.list_basis(
            collection_name, query, limit
        )
        for value in values:
            items.append(
                {
                    "artifact_type": kind,
                    "artifact_id": value["_id"],
                    "artifact_version_id": value["_id"]
                    if kind.endswith('VERSION')
                    else None,
                    "title": value.get("title")
                    or value.get("name")
                    or value.get("filename")
                    or value["_id"],
                    "status": value.get("status"),
                }
            )
    return {"items": items[:limit], "total": min(len(items), limit)}


def deterministic_testability_findings(basis_snapshots):
    findings = []
    for snapshot in basis_snapshots:
        text = str(snapshot.get("text") or "").strip()
        evidence = [
            {
                "artifact_type": snapshot["artifact_type"],
                "artifact_id": snapshot["artifact_id"],
                "artifact_version_id": snapshot.get("artifact_version_id")
                or snapshot.get("resolved_id"),
            }
        ]
        rules = evaluate_rules("test_basis", {"text": text})
        for index, rule in enumerate(rules, 1):
            findings.append(
                {
                    "candidate_id": (
                        f"{'DET-'}"
                        f"{snapshot['resolved_id']}-{index}"
                    ),
                    "category": rule["category"],
                    "severity": rule["severity"],
                    "title": rule["message"],
                    "description": rule["message"],
                    "suggestion": rule["suggestion"],
                    "evidence_refs": evidence,
                    "reason_codes": [rule["rule_id"]],
                    "candidate_only": True,
                }
            )
    return findings
