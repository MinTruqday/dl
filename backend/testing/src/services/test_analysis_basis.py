import re

from fastapi import HTTPException

from src.core.common import get_project
from src.repositories import requirement_analysis_repository
from src.services.domain_policy import domain_policy
from src.services.quality_policy import evaluate_rules


BASIS_POLICY = domain_policy("test_analysis_basis")
BASIS_COLLECTIONS = BASIS_POLICY["collections"]


def basis_text(value):
    for field in BASIS_POLICY["text_fields"]:
        if value.get(field):
            return str(value[field])[: int(BASIS_POLICY["maximum_text_characters"])]
    return ""


async def resolve_basis(project_id, refs):
    snapshots = []
    seen = set()
    for ref in refs:
        key = (ref.artifact_type, ref.artifact_id, ref.artifact_version_id)
        if key in seen:
            raise HTTPException(status_code=422, detail={"code": BASIS_POLICY["duplicate_ref_code"]})
        seen.add(key)
        collection = BASIS_COLLECTIONS[ref.artifact_type]
        identifier = ref.artifact_version_id or ref.artifact_id
        query = {"_id": identifier, "project_id": project_id}
        if ref.artifact_type == BASIS_POLICY["regulation_type"]:
            query["source_type"] = BASIS_POLICY["regulation_type"]
        value = await requirement_analysis_repository.find_basis(collection, query)
        if not value:
            global_query = {"_id": identifier}
            if ref.artifact_type == BASIS_POLICY["regulation_type"]:
                global_query["source_type"] = BASIS_POLICY["regulation_type"]
            exists = await requirement_analysis_repository.find_basis(
                collection, global_query, {"_id": 1}
            )
            code = (
                BASIS_POLICY["project_mismatch_code"]
                if exists
                else BASIS_POLICY["not_found_code"]
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
        if ref.artifact_type == BASIS_POLICY["requirement_version_type"]:
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
    types = [artifact_type] if artifact_type else list(BASIS_COLLECTIONS)
    items = []
    for kind in types:
        collection_name = BASIS_COLLECTIONS.get(kind)
        if not collection_name:
            raise HTTPException(status_code=422, detail={"code": BASIS_POLICY["invalid_type_code"]})
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
                    if kind.endswith(BASIS_POLICY["version_suffix"])
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
                        f"{BASIS_POLICY['candidate_id_prefix']}"
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
