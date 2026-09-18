import json
import re

from fastapi import HTTPException
from pydantic import ValidationError
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, next_key, now, page_payload
from src.core.database import database
from src.domain.test_analysis import TestConditionCreate, condition_hash, condition_snapshot
from src.repositories.test_condition import test_condition_repository
from src.services.design_assistance import ai_contract_metadata, request_design_assistance

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
    for field in (
        "plain_text_projection",
        "plain_text",
        "normalized_content",
        "description",
        "title",
        "name",
    ):
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
            global_query = {"_id": identifier}
            if ref.artifact_type == "REGULATION":
                global_query["source_type"] = "REGULATION"
            exists = await database.value[collection].find_one(global_query, {"_id": 1})
            code = "TEST_BASIS_PROJECT_MISMATCH" if exists else "TEST_BASIS_NOT_FOUND"
            raise HTTPException(
                status_code=422,
                detail={
                    "code": code,
                    "artifact_type": ref.artifact_type,
                    "artifact_id": identifier,
                },
            )
        text = basis_text(value)
        if ref.artifact_type == "REQUIREMENT_VERSION":
            criteria = await database.value.acceptance_criteria.find(
                {"requirement_version_id": identifier, "project_id": project_id}
            ).to_list(200)
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


async def get_condition_for_user(condition_id, user, permission="testcondition.read"):
    condition = await test_condition_repository.get(condition_id)
    if not condition:
        raise HTTPException(status_code=404, detail={"code": "TEST_CONDITION_NOT_FOUND"})
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
    for field, value in {
        "status": status,
        "risk": risk,
        "testability_status": testability_status,
    }.items():
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
        "condition_key": payload.condition_key
        or await next_key(project_id, "test_condition", "TCON"),
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
        raise HTTPException(
            status_code=409, detail={"code": "TEST_CONDITION_KEY_EXISTS"}
        ) from error
    await audit(
        user.id,
        "test_condition_created",
        "TestCondition",
        value["_id"],
        project_id,
        {"basis_count": len(basis_snapshots), "origin": value["origin"]},
    )
    return value


async def update_condition(condition_id, payload, user):
    condition = await get_condition_for_user(condition_id, user, "testcondition.update")
    if condition["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "TEST_CONDITION_IMMUTABLE"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if payload.basis_refs is not None:
        changes["basis_snapshots"] = await resolve_basis(
            condition["project_id"], payload.basis_refs
        )
    TestConditionCreate.model_validate({**condition, **changes})
    changes["updated_at"] = now()
    updated = await test_condition_repository.update(
        condition_id, condition["project_id"], payload.expected_revision, {"DRAFT"}, changes
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "test_condition_updated",
        "TestCondition",
        condition_id,
        condition["project_id"],
        {"fields": sorted(field for field in changes if field != "updated_at")},
    )
    return updated


async def transition_condition(condition_id, payload, user, action):
    permission = (
        "testcondition.review"
        if action == "submit"
        else "testcondition.approve"
        if action == "approve"
        else "testcondition.archive"
    )
    condition = await get_condition_for_user(condition_id, user, permission)
    transitions = {
        "submit": ({"DRAFT"}, "IN_REVIEW"),
        "approve": ({"IN_REVIEW"}, "APPROVED"),
        "archive": ({"DRAFT", "APPROVED"}, "ARCHIVED"),
    }
    sources, target = transitions[action]
    if action in {"submit", "approve"}:
        try:
            TestConditionCreate.model_validate(condition)
        except ValidationError as error:
            raise HTTPException(
                status_code=409, detail={"code": "TEST_CONDITION_INCOMPLETE"}
            ) from error
    changes = {"status": target, "updated_at": now()}
    if action == "submit":
        changes.update(
            {"submitted_by": user.id, "submitted_at": now(), "review_note": payload.note}
        )
    elif action == "approve":
        open_blockers = [
            finding
            for finding in condition.get("analysis_findings", [])
            if finding.get("status") == "OPEN" and finding.get("severity") in {"CRITICAL", "HIGH"}
        ]
        if open_blockers:
            raise HTTPException(status_code=409, detail={"code": "OPEN_TESTABILITY_FINDINGS"})
        changes.update(
            {
                "approved_by": user.id,
                "approved_at": now(),
                "approved_snapshot": condition_snapshot(condition),
                "approved_snapshot_hash": condition_hash(condition),
                "approval_history": [
                    *condition.get("approval_history", []),
                    {"actor_id": user.id, "action": "APPROVED", "note": payload.note, "at": now()},
                ],
            }
        )
    else:
        changes.update(
            {"archived_by": user.id, "archived_at": now(), "archive_reason": payload.note}
        )
    updated = await test_condition_repository.update(
        condition_id, condition["project_id"], payload.expected_revision, sources, changes
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "TEST_CONDITION_TRANSITION_CONFLICT"})
    event = {
        "submit": "test_condition_submitted",
        "approve": "test_condition_approved",
        "archive": "test_condition_archived",
    }[action]
    await audit(
        user.id,
        event,
        "TestCondition",
        condition_id,
        condition["project_id"],
        {"from": condition["status"], "to": target, "note": payload.note},
    )
    return updated


async def resolve_finding(condition_id, finding_id, payload, user):
    condition = await get_condition_for_user(condition_id, user, "testanalysis.resolve_finding")
    if condition["status"] == "ARCHIVED":
        raise HTTPException(
            status_code=409, detail={"code": "ARTIFACT_ARCHIVED", "artifact_type": "TEST_CONDITION"}
        )
    found = False
    findings = []
    for finding in condition.get("analysis_findings", []):
        if finding.get("finding_id") != finding_id:
            findings.append(finding)
            continue
        found = True
        if finding.get("status") != "OPEN":
            raise HTTPException(
                status_code=409, detail={"code": "ANALYSIS_FINDING_ALREADY_RESOLVED"}
            )
        findings.append(
            {
                **finding,
                "status": payload.status,
                "resolved_by": user.id,
                "resolved_at": now(),
                "resolution_ref": payload.resolution_ref,
                "resolution_note": payload.note,
            }
        )
    if not found:
        raise HTTPException(status_code=404, detail={"code": "FINDING_NOT_FOUND"})
    updated = await test_condition_repository.update(
        condition_id,
        condition["project_id"],
        payload.expected_revision,
        {"DRAFT", "IN_REVIEW", "APPROVED"},
        {"analysis_findings": findings, "updated_at": now()},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "test_analysis_finding_resolved",
        "TestCondition",
        condition_id,
        condition["project_id"],
        {
            "finding_id": finding_id,
            "status": payload.status,
            "resolution_ref": payload.resolution_ref,
        },
    )
    return updated


async def run_ai_analysis(project_id, payload, user):
    await get_project(project_id, user, "testanalysis.run_ai")
    existing = await database.value.ai_results.find_one(
        {"project_id": project_id, "idempotency_key": payload.idempotency_key}
    )
    if existing:
        if existing.get("result_type") != "TEST_CONDITION_CANDIDATES":
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
        return existing
    basis_snapshots = await resolve_basis(project_id, payload.basis_refs)
    evidence = [
        {
            "artifact_type": item["artifact_type"],
            "artifact_id": item["artifact_id"],
            "artifact_version_id": item.get("artifact_version_id") or item["resolved_id"],
            "authority": "PROJECT_BASELINE",
            "text": item["text"],
        }
        for item in basis_snapshots
    ]
    instruction = json.dumps(
        {
            "task": "Đề xuất test condition và finding về khả năng kiểm thử chỉ từ bằng chứng không phê duyệt hay sửa artifact",
            "user_instruction": payload.instruction,
            "required_finding_fields": [
                "category",
                "severity",
                "statement",
                "evidence_refs",
                "reason_codes",
                "suggestion",
            ],
            "required_condition_fields": [
                "title",
                "coverage_item",
                "test_level",
                "test_type",
                "risk",
                "priority",
                "technique_candidates",
                "testability_status",
            ],
        },
        ensure_ascii=False,
    )
    ai_result = await request_design_assistance(
        "test_condition_generation", project_id, instruction, evidence
    )
    candidates = [
        {
            **item,
            "candidate_id": f"TCON-CAND-{index}",
            "status": "CANDIDATE",
            "candidate_only": True,
            "basis_refs": [ref.model_dump() for ref in payload.basis_refs],
        }
        for index, item in enumerate(ai_result.get("suggestions", []), 1)
    ]
    findings = [
        {
            **item,
            "candidate_id": f"TFIND-CAND-{index}",
            "status": "CANDIDATE",
            "candidate_only": True,
        }
        for index, item in enumerate(ai_result.get("findings", []), 1)
    ]
    value = {
        "_id": new_id("AIR"),
        "project_id": project_id,
        "result_type": "TEST_CONDITION_CANDIDATES",
        "candidates": candidates,
        "findings": findings,
        "basis_snapshots": basis_snapshots,
        "candidate_only": True,
        "human_confirmation_required": True,
        **ai_contract_metadata(ai_result),
        "idempotency_key": payload.idempotency_key,
        "created_by": user.id,
        "created_at": now(),
    }
    try:
        await database.value.ai_results.insert_one(value)
    except DuplicateKeyError:
        return await database.value.ai_results.find_one(
            {"project_id": project_id, "idempotency_key": payload.idempotency_key}
        )
    await audit(
        user.id,
        "test_analysis_ai_candidates_generated",
        "AIResult",
        value["_id"],
        project_id,
        {"candidate_count": len(candidates), "status": value["status"]},
    )
    return value


async def condition_coverage(project_id, user):
    await get_project(project_id, user, "testcondition.read")
    conditions = await database.value.test_conditions.find(
        {"project_id": project_id, "status": {"$ne": "ARCHIVED"}}
    ).to_list(5000)
    condition_ids = [item["_id"] for item in conditions]
    scenarios = await database.value.test_scenarios.find(
        {"project_id": project_id, "test_condition_ids": {"$in": condition_ids}}
    ).to_list(5000)
    case_versions = await database.value.test_case_versions.find(
        {
            "project_id": project_id,
            "$or": [
                {"test_condition_ids": {"$in": condition_ids}},
                {"scenario_id": {"$in": [item["_id"] for item in scenarios]}},
            ],
        }
    ).to_list(10000)
    rows = []
    for condition in conditions:
        linked_scenarios = [
            item["_id"]
            for item in scenarios
            if condition["_id"] in item.get("test_condition_ids", [])
        ]
        linked_cases = [
            item["_id"]
            for item in case_versions
            if condition["_id"] in item.get("test_condition_ids", [])
            or item.get("scenario_id") in linked_scenarios
        ]
        rows.append(
            {
                "condition_id": condition["_id"],
                "condition_key": condition["condition_key"],
                "title": condition["title"],
                "basis_refs": condition["basis_refs"],
                "scenario_ids": linked_scenarios,
                "test_case_version_ids": linked_cases,
                "uncovered": not linked_cases,
            }
        )
    return {
        "items": rows,
        "condition_count": len(rows),
        "uncovered_count": sum(item["uncovered"] for item in rows),
    }


async def list_test_basis(project_id, user, artifact_type="", query_text="", limit=200):
    await get_project(project_id, user, "testanalysis.read")
    types = [artifact_type] if artifact_type else list(BASIS_COLLECTIONS)
    items = []
    for kind in types:
        collection_name = BASIS_COLLECTIONS.get(kind)
        if not collection_name:
            raise HTTPException(status_code=422, detail={"code": "TEST_BASIS_TYPE_INVALID"})
        query = {"project_id": project_id}
        if query_text:
            pattern = {"$regex": re.escape(query_text), "$options": "i"}
            query["$or"] = [
                {"title": pattern},
                {"name": pattern},
                {"plain_text_projection": pattern},
            ]
        values = await database.value[collection_name].find(query).limit(limit).to_list(limit)
        for value in values:
            items.append(
                {
                    "artifact_type": kind,
                    "artifact_id": value["_id"],
                    "artifact_version_id": value["_id"] if kind.endswith("VERSION") else None,
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
        lowered = text.lower()
        evidence = [
            {
                "artifact_type": snapshot["artifact_type"],
                "artifact_id": snapshot["artifact_id"],
                "artifact_version_id": snapshot.get("artifact_version_id")
                or snapshot.get("resolved_id"),
            }
        ]
        rules = []
        if not text:
            rules.append(
                ("UNTESTABLE", "BLOCKER", "Nội dung kiểm thử đang trống", "EMPTY_EXPECTED_BEHAVIOR")
            )
        if re.search(r"\b(todo|tbd|fixme|chưa xác định)\b", lowered):
            rules.append(
                (
                    "OMISSION",
                    "MAJOR",
                    "Nội dung còn placeholder chưa được giải quyết",
                    "UNRESOLVED_PLACEHOLDER",
                )
            )
        if any(word in lowered for word in ("quyền", "permission", "vai trò", "role")) and not any(
            word in lowered
            for word in (
                "người dùng",
                "quản trị",
                "kiểm thử",
                "developer",
                "tester",
                "admin",
                "actor",
            )
        ):
            rules.append(
                (
                    "MISSING_PERMISSION_RULE",
                    "MAJOR",
                    "Quy tắc quyền chưa xác định actor",
                    "PERMISSION_ACTOR_MISSING",
                )
            )
        if re.search(r"\d", text) and not any(
            word in lowered
            for word in (
                "tối đa",
                "tối thiểu",
                "lớn hơn",
                "nhỏ hơn",
                "không quá",
                "ít nhất",
                "maximum",
                "minimum",
            )
        ):
            rules.append(
                (
                    "MISSING_BOUNDARY",
                    "MINOR",
                    "Giá trị số chưa mô tả điều kiện biên",
                    "NUMERIC_BOUNDARY_MISSING",
                )
            )
        if any(
            word in lowered
            for word in ("hiệu năng", "performance", "thời gian phản hồi", "throughput")
        ) and not re.search(r"\d", text):
            rules.append(
                (
                    "MISSING_NON_FUNCTIONAL_CRITERIA",
                    "MAJOR",
                    "Yêu cầu phi chức năng chưa có mục tiêu đo được",
                    "NFR_TARGET_MISSING",
                )
            )
        for index, (category, severity, description, reason_code) in enumerate(rules, 1):
            findings.append(
                {
                    "candidate_id": f"DET-{snapshot['resolved_id']}-{index}",
                    "category": category,
                    "severity": severity,
                    "title": description,
                    "description": description,
                    "suggestion": "Bổ sung tiêu chí quan sát được và có thể kiểm chứng",
                    "evidence_refs": evidence,
                    "reason_codes": [reason_code],
                    "candidate_only": True,
                }
            )
    return findings


async def run_deterministic_analysis(project_id, payload, user):
    await get_project(project_id, user, "testanalysis.execute")
    snapshots = await resolve_basis(project_id, payload.basis_refs)
    findings = deterministic_testability_findings(snapshots)
    await audit(
        user.id,
        "test_analysis_executed",
        "Project",
        project_id,
        project_id,
        {
            "basis_count": len(snapshots),
            "finding_count": len(findings),
            "engine": "deterministic-v1",
        },
    )
    return {
        "status": "SUCCESS",
        "engine": "deterministic-v1",
        "findings": findings,
        "basis_snapshots": snapshots,
    }


async def list_analysis_findings(project_id, user, status="", limit=500):
    await get_project(project_id, user, "testanalysis.read")
    query = {"project_id": project_id}
    if status:
        query["status"] = status
    items = (
        await database.value.test_analysis_findings.find(query)
        .sort("updated_at", -1)
        .limit(limit)
        .to_list(limit)
    )
    return {"items": items, "total": len(items)}


async def create_analysis_finding(project_id, payload, user):
    await get_project(project_id, user, "testanalysis.finding.create")
    ref_type = payload.artifact_type.upper()
    collection_name = BASIS_COLLECTIONS.get(ref_type)
    if not collection_name:
        raise HTTPException(status_code=422, detail={"code": "TEST_BASIS_TYPE_INVALID"})
    identifier = payload.artifact_version_id or payload.artifact_id
    if not await database.value[collection_name].find_one(
        {"_id": identifier, "project_id": project_id}, {"_id": 1}
    ):
        raise HTTPException(status_code=422, detail={"code": "CROSS_PROJECT_REFERENCE"})
    timestamp = now()
    value = {
        "_id": new_id("AFND"),
        "project_id": project_id,
        **payload.model_dump(),
        "status": "OPEN",
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await database.value.test_analysis_findings.insert_one(value)
    await audit(
        user.id,
        "analysis_finding_created",
        "AnalysisFinding",
        value["_id"],
        project_id,
        {"category": value["category"], "severity": value["severity"]},
    )
    return value


async def assign_analysis_finding(finding_id, payload, user):
    finding = await database.value.test_analysis_findings.find_one({"_id": finding_id})
    if not finding:
        raise HTTPException(status_code=404, detail={"code": "ANALYSIS_FINDING_NOT_FOUND"})
    await get_project(finding["project_id"], user, "testanalysis.finding.assign")
    member = await database.value.project_members.find_one(
        {"project_id": finding["project_id"], "user_id": payload.owner_id, "status": "ACTIVE"}
    )
    if not member:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MEMBER_NOT_FOUND"})
    updated = await database.value.test_analysis_findings.find_one_and_update(
        {
            "_id": finding_id,
            "revision": payload.expected_revision,
            "status": {"$in": ["OPEN", "IN_PROGRESS"]},
        },
        {
            "$set": {"owner_id": payload.owner_id, "status": "IN_PROGRESS", "updated_at": now()},
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "STALE_REVISION"})
    await audit(
        user.id,
        "analysis_finding_assigned",
        "AnalysisFinding",
        finding_id,
        finding["project_id"],
        {"owner_id": payload.owner_id},
    )
    return updated


async def transition_analysis_finding(finding_id, payload, user, verify=False):
    finding = await database.value.test_analysis_findings.find_one({"_id": finding_id})
    if not finding:
        raise HTTPException(status_code=404, detail={"code": "ANALYSIS_FINDING_NOT_FOUND"})
    permission = "testanalysis.verify_finding" if verify else "testanalysis.resolve_finding"
    await get_project(finding["project_id"], user, permission)
    if (verify and finding.get("status") != "RESOLVED") or (
        not verify and finding.get("status") not in {"OPEN", "IN_PROGRESS"}
    ):
        if finding.get("status") in {"RESOLVED", "VERIFIED", "ACCEPTED_RISK"}:
            raise HTTPException(
                status_code=409, detail={"code": "ANALYSIS_FINDING_ALREADY_RESOLVED"}
            )
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    source = "RESOLVED" if verify else {"$in": ["OPEN", "IN_PROGRESS"]}
    target = "VERIFIED" if verify else "RESOLVED"
    changes = {
        "status": target,
        "updated_at": now(),
        "resolution": payload.resolution,
        "resolution_ref": payload.resolution_ref,
    }
    changes["verified_by" if verify else "resolved_by"] = user.id
    changes["verified_at" if verify else "resolved_at"] = now()
    updated = await database.value.test_analysis_findings.find_one_and_update(
        {"_id": finding_id, "revision": payload.expected_revision, "status": source},
        {"$set": changes, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    await audit(
        user.id,
        "analysis_finding_verified" if verify else "analysis_finding_resolved",
        "AnalysisFinding",
        finding_id,
        finding["project_id"],
        {},
    )
    return updated


async def review_condition(condition_id, payload, user):
    condition = await get_condition_for_user(condition_id, user, "testcondition.review")
    updated = await test_condition_repository.update(
        condition_id,
        condition["project_id"],
        payload.expected_revision,
        {"IN_REVIEW"},
        {
            "reviewed_by": list(dict.fromkeys([*condition.get("reviewed_by", []), user.id])),
            "review_note": payload.note,
            "updated_at": now(),
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "STALE_REVISION"})
    await audit(
        user.id,
        "test_condition_reviewed",
        "TestCondition",
        condition_id,
        condition["project_id"],
        {"note": payload.note},
    )
    return updated


async def bulk_prioritize_conditions(project_id, payload, user):
    await get_project(project_id, user, "testcondition.bulk.update")
    results = []
    for item in payload.items:
        condition = await test_condition_repository.get(item["condition_id"], project_id)
        if not condition:
            raise HTTPException(status_code=404, detail={"code": "TEST_CONDITION_NOT_FOUND"})
        updated = await test_condition_repository.update(
            item["condition_id"],
            project_id,
            int(item["expected_revision"]),
            {"DRAFT"},
            {"priority": item["priority"], "updated_at": now()},
        )
        if not updated:
            raise HTTPException(
                status_code=409,
                detail={"code": "STALE_REVISION", "condition_id": item["condition_id"]},
            )
        results.append(updated)
        await audit(
            user.id,
            "test_condition_updated",
            "TestCondition",
            item["condition_id"],
            project_id,
            {"fields": ["priority"]},
        )
    return {"items": results, "total": len(results)}
