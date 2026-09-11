import json
import re

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, next_key, now, page_payload
from src.core.database import database
from src.domain.test_analysis import TestConditionCreate, condition_hash, condition_snapshot
from src.repositories.test_condition import test_condition_repository
from src.services.design_assistance import request_design_assistance


BASIS_COLLECTIONS = {
    "REQUIREMENT_VERSION": "requirement_versions",
    "ACCEPTANCE_CRITERION": "acceptance_criteria",
    "API_OPERATION": "api_operations",
    "KNOWLEDGE_SOURCE": "requirement_documents",
    "BUSINESS_RULE": "business_rules",
    "RISK_RANKING": "risk_rankings",
    "DEFECT": "defects",
    "REGULATION": "requirement_documents",
}


def basis_text(value):
    for field in ("plain_text_projection", "plain_text", "normalized_content", "description", "title", "name"):
        if value.get(field):
            return str(value[field])[:4000]
    return ""


async def resolve_basis(project_id, refs):
    snapshots = []
    seen = set()
    for ref in refs:
        key = (ref.artifact_type, ref.artifact_id, ref.artifact_version_id)
        if key in seen:
            raise HTTPException(status_code=422, detail={"code": "DUPLICATE_TEST_BASIS_REF"})
        seen.add(key)
        collection = BASIS_COLLECTIONS[ref.artifact_type]
        identifier = ref.artifact_version_id or ref.artifact_id
        query = {"_id": identifier, "project_id": project_id}
        if ref.artifact_type == "REGULATION":
            query["source_type"] = "REGULATION"
        value = await database.value[collection].find_one(query)
        if not value:
            raise HTTPException(status_code=422, detail={"code": "CROSS_PROJECT_OR_MISSING_TEST_BASIS", "artifact_type": ref.artifact_type, "artifact_id": identifier})
        snapshots.append(
            {
                **ref.model_dump(),
                "resolved_id": identifier,
                "title": value.get("title") or value.get("name") or value.get("filename") or identifier,
                "status": value.get("status"),
                "source_hash": value.get("normalized_content_hash") or value.get("content_hash"),
                "text": basis_text(value),
            }
        )
    return snapshots


async def get_condition_for_user(condition_id, user, permission="testcondition.read"):
    condition = await test_condition_repository.get(condition_id)
    if not condition:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(condition["project_id"], user, permission)
    return condition


async def list_conditions(project_id, user, q, status, risk, testability_status, page, page_size):
    await get_project(project_id, user, "testcondition.read")
    query = {"project_id": project_id}
    if q:
        query["$or"] = [
            {"condition_key": {"$regex": re.escape(q), "$options": "i"}},
            {"title": {"$regex": re.escape(q), "$options": "i"}},
            {"coverage_item": {"$regex": re.escape(q), "$options": "i"}},
        ]
    for field, value in {"status": status, "risk": risk, "testability_status": testability_status}.items():
        if value:
            query[field] = value
    items, total = await test_condition_repository.list(query, (page - 1) * page_size, page_size)
    return page_payload(items, page, page_size, total)


async def create_condition(project_id, payload, user):
    await get_project(project_id, user, "testcondition.create")
    basis_snapshots = await resolve_basis(project_id, payload.basis_refs)
    timestamp = now()
    value = {
        "_id": new_id("TCON"),
        "project_id": project_id,
        **payload.model_dump(),
        "condition_key": payload.condition_key or await next_key(project_id, "test_condition", "TCON"),
        "basis_snapshots": basis_snapshots,
        "status": "DRAFT",
        "reviewed_by": [],
        "approval_history": [],
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await test_condition_repository.create(value)
    except DuplicateKeyError as error:
        raise HTTPException(status_code=409, detail={"code": "TEST_CONDITION_KEY_EXISTS"}) from error
    await audit(user.id, "test_condition_created", "TestCondition", value["_id"], project_id, {"basis_count": len(basis_snapshots), "origin": value["origin"]})
    return value


async def update_condition(condition_id, payload, user):
    condition = await get_condition_for_user(condition_id, user, "testcondition.update")
    if condition["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "TEST_CONDITION_IMMUTABLE"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if payload.basis_refs is not None:
        changes["basis_snapshots"] = await resolve_basis(condition["project_id"], payload.basis_refs)
    TestConditionCreate.model_validate({**condition, **changes})
    changes["updated_at"] = now()
    updated = await test_condition_repository.update(condition_id, condition["project_id"], payload.expected_revision, {"DRAFT"}, changes)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "test_condition_updated", "TestCondition", condition_id, condition["project_id"], {"fields": sorted(field for field in changes if field != "updated_at")})
    return updated


async def transition_condition(condition_id, payload, user, action):
    permission = "testcondition.review" if action == "submit" else "testcondition.approve" if action == "approve" else "testcondition.archive"
    condition = await get_condition_for_user(condition_id, user, permission)
    transitions = {
        "submit": ({"DRAFT"}, "IN_REVIEW"),
        "approve": ({"IN_REVIEW"}, "APPROVED"),
        "archive": ({"DRAFT", "APPROVED"}, "ARCHIVED"),
    }
    sources, target = transitions[action]
    changes = {"status": target, "updated_at": now()}
    if action == "submit":
        changes.update({"submitted_by": user.id, "submitted_at": now(), "review_note": payload.note})
    elif action == "approve":
        open_blockers = [finding for finding in condition.get("analysis_findings", []) if finding.get("status") == "OPEN" and finding.get("severity") in {"CRITICAL", "HIGH"}]
        if open_blockers:
            raise HTTPException(status_code=409, detail={"code": "OPEN_TESTABILITY_FINDINGS"})
        changes.update({"approved_by": user.id, "approved_at": now(), "approved_snapshot": condition_snapshot(condition), "approved_snapshot_hash": condition_hash(condition), "approval_history": [*condition.get("approval_history", []), {"actor_id": user.id, "action": "APPROVED", "note": payload.note, "at": now()}]})
    else:
        changes.update({"archived_by": user.id, "archived_at": now(), "archive_reason": payload.note})
    updated = await test_condition_repository.update(condition_id, condition["project_id"], payload.expected_revision, sources, changes)
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "TEST_CONDITION_TRANSITION_CONFLICT"})
    await audit(user.id, f"test_condition_{action}", "TestCondition", condition_id, condition["project_id"], {"from": condition["status"], "to": target, "note": payload.note})
    return updated


async def resolve_finding(condition_id, finding_id, payload, user):
    condition = await get_condition_for_user(condition_id, user, "testanalysis.resolve_finding")
    if condition["status"] == "ARCHIVED":
        raise HTTPException(status_code=409, detail={"code": "TEST_CONDITION_ARCHIVED"})
    found = False
    findings = []
    for finding in condition.get("analysis_findings", []):
        if finding.get("finding_id") != finding_id:
            findings.append(finding)
            continue
        found = True
        if finding.get("status") != "OPEN":
            raise HTTPException(status_code=409, detail={"code": "FINDING_ALREADY_RESOLVED"})
        findings.append({**finding, "status": payload.status, "resolved_by": user.id, "resolved_at": now(), "resolution_ref": payload.resolution_ref, "resolution_note": payload.note})
    if not found:
        raise HTTPException(status_code=404, detail={"code": "FINDING_NOT_FOUND"})
    updated = await test_condition_repository.update(condition_id, condition["project_id"], payload.expected_revision, {"DRAFT", "IN_REVIEW", "APPROVED"}, {"analysis_findings": findings, "updated_at": now()})
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "test_analysis_finding_resolved", "TestCondition", condition_id, condition["project_id"], {"finding_id": finding_id, "status": payload.status, "resolution_ref": payload.resolution_ref})
    return updated


async def run_ai_analysis(project_id, payload, user):
    await get_project(project_id, user, "testanalysis.run_ai")
    existing = await database.value.ai_results.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
    if existing:
        if existing.get("result_type") != "TEST_CONDITION_CANDIDATES":
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
        return existing
    basis_snapshots = await resolve_basis(project_id, payload.basis_refs)
    evidence = [{"artifact_type": item["artifact_type"], "artifact_id": item["artifact_id"], "artifact_version_id": item.get("artifact_version_id") or item["resolved_id"], "authority": "PROJECT_BASELINE", "text": item["text"]} for item in basis_snapshots]
    instruction = json.dumps({"task": "Đề xuất test condition và finding về khả năng kiểm thử chỉ từ bằng chứng không phê duyệt hay sửa artifact", "user_instruction": payload.instruction, "required_condition_fields": ["title", "coverage_item", "test_level", "test_type", "risk", "priority", "technique_candidates", "testability_status", "analysis_findings"]}, ensure_ascii=False)
    ai_result = await request_design_assistance("test_condition_generation", project_id, instruction, evidence)
    candidates = [{**item, "candidate_id": f"TCON-CAND-{index}", "status": "CANDIDATE", "candidate_only": True, "basis_refs": [ref.model_dump() for ref in payload.basis_refs]} for index, item in enumerate(ai_result.get("suggestions", []), 1)]
    value = {
        "_id": new_id("AIR"),
        "project_id": project_id,
        "result_type": "TEST_CONDITION_CANDIDATES",
        "candidates": candidates,
        "basis_snapshots": basis_snapshots,
        "candidate_only": True,
        "human_confirmation_required": True,
        "status": ai_result.get("status", "DEGRADED"),
        "degraded_mode": ai_result.get("degraded_mode"),
        "warnings": ai_result.get("warnings", []),
        "confidence": ai_result.get("confidence", 0),
        "model": ai_result.get("model", {}),
        "idempotency_key": payload.idempotency_key,
        "created_by": user.id,
        "created_at": now(),
    }
    try:
        await database.value.ai_results.insert_one(value)
    except DuplicateKeyError:
        return await database.value.ai_results.find_one({"project_id": project_id, "idempotency_key": payload.idempotency_key})
    await audit(user.id, "test_analysis_ai_candidates_generated", "AIResult", value["_id"], project_id, {"candidate_count": len(candidates), "status": value["status"]})
    return value


async def condition_coverage(project_id, user):
    await get_project(project_id, user, "testcondition.read")
    conditions = await database.value.test_conditions.find({"project_id": project_id, "status": {"$ne": "ARCHIVED"}}).to_list(5000)
    condition_ids = [item["_id"] for item in conditions]
    scenarios = await database.value.test_scenarios.find({"project_id": project_id, "test_condition_ids": {"$in": condition_ids}}).to_list(5000)
    case_versions = await database.value.test_case_versions.find({"project_id": project_id, "$or": [{"test_condition_ids": {"$in": condition_ids}}, {"scenario_id": {"$in": [item["_id"] for item in scenarios]}}]}).to_list(10000)
    rows = []
    for condition in conditions:
        linked_scenarios = [item["_id"] for item in scenarios if condition["_id"] in item.get("test_condition_ids", [])]
        linked_cases = [item["_id"] for item in case_versions if condition["_id"] in item.get("test_condition_ids", []) or item.get("scenario_id") in linked_scenarios]
        rows.append({"condition_id": condition["_id"], "condition_key": condition["condition_key"], "title": condition["title"], "basis_refs": condition["basis_refs"], "scenario_ids": linked_scenarios, "test_case_version_ids": linked_cases, "uncovered": not linked_cases})
    return {"items": rows, "condition_count": len(rows), "uncovered_count": sum(item["uncovered"] for item in rows)}
