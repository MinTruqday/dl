import json
import re

from fastapi import HTTPException
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, next_key, now, page_payload
from src.domain.test_analysis import TestConditionCreate, condition_hash, condition_snapshot
from src.repositories.test_condition import test_condition_repository
from src.repositories.test_analysis import test_analysis_repository
from src.services.domain_policy import domain_policy
from src.services.design_assistance import ai_contract_metadata, request_design_assistance
from src.services.test_analysis_basis import (
    BASIS_COLLECTIONS,
    deterministic_testability_findings,
    list_test_basis,
    resolve_basis,
)

TEST_ANALYSIS_POLICY = domain_policy("test_analysis")

__all__ = ["list_test_basis"]


async def get_condition_for_user(condition_id, user, permission=None):
    policy = TEST_ANALYSIS_POLICY
    condition = await test_condition_repository.get(condition_id)
    if not condition:
        raise HTTPException(
            status_code=404,
            detail={"code": policy["error_codes"]["condition_not_found"]},
        )
    await get_project(
        condition["project_id"],
        user,
        permission or policy["permissions"]["condition_read"],
    )
    return condition


async def list_conditions(project_id, user, q, status, risk, testability_status, page, page_size):
    await get_project(
        project_id, user, TEST_ANALYSIS_POLICY["permissions"]["condition_read"]
    )
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
    policy = TEST_ANALYSIS_POLICY
    await get_project(project_id, user, policy["permissions"]["condition_create"])
    basis_snapshots = await resolve_basis(project_id, payload.basis_refs)
    timestamp = now()
    value = {
        "_id": new_id(policy["condition_id_prefix"]),
        "project_id": project_id,
        **payload.model_dump(),
        "condition_key": payload.condition_key
        or await next_key(
            project_id, policy["condition_counter"], policy["condition_id_prefix"]
        ),
        "basis_snapshots": basis_snapshots,
        "status": policy["draft_status"],
        "reviewed_by": [],
        "approval_history": [],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await test_condition_repository.create(value)
    except DuplicateKeyError as error:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["error_codes"]["condition_key_exists"]},
        ) from error
    await audit(
        user.id,
        policy["events"]["condition_created"],
        policy["condition_entity_type"],
        value["_id"],
        project_id,
        {"basis_count": len(basis_snapshots), "origin": value["origin"]},
    )
    return value


async def update_condition(condition_id, payload, user):
    policy = TEST_ANALYSIS_POLICY
    condition = await get_condition_for_user(
        condition_id, user, policy["permissions"]["condition_update"]
    )
    if condition["status"] != policy["draft_status"]:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["error_codes"]["condition_immutable"]},
        )
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if payload.basis_refs is not None:
        changes["basis_snapshots"] = await resolve_basis(
            condition["project_id"], payload.basis_refs
        )
    TestConditionCreate.model_validate({**condition, **changes})
    changes["updated_at"] = now()
    updated = await test_condition_repository.update(
        condition_id,
        condition["project_id"],
        payload.expected_revision,
        {policy["draft_status"]},
        changes,
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["revision_conflict"]}
        )
    await audit(
        user.id,
        policy["events"]["condition_updated"],
        policy["condition_entity_type"],
        condition_id,
        condition["project_id"],
        {"fields": sorted(field for field in changes if field != "updated_at")},
    )
    return updated


async def transition_condition(condition_id, payload, user, action):
    policy = TEST_ANALYSIS_POLICY
    transition = policy["condition_transitions"][action]
    condition = await get_condition_for_user(
        condition_id, user, transition["permission"]
    )
    sources = set(transition["sources"])
    target = transition["target"]
    if action in {"submit", "approve"}:
        try:
            TestConditionCreate.model_validate(condition)
        except ValidationError as error:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["error_codes"]["condition_incomplete"]},
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
            if finding.get("status") == policy["open_status"]
            and finding.get("severity") in set(policy["finding_blocking_severities"])
        ]
        if open_blockers:
            raise HTTPException(
                status_code=409, detail={"code": policy["error_codes"]["open_findings"]}
            )
        changes.update(
            {
                "approved_by": user.id,
                "approved_at": now(),
                "approved_snapshot": condition_snapshot(condition),
                "approved_snapshot_hash": condition_hash(condition),
                "approval_history": [
                    *condition.get("approval_history", []),
                    {
                        "actor_id": user.id,
                        "action": policy["approval_action"],
                        "note": payload.note,
                        "at": now(),
                    },
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
        raise HTTPException(
            status_code=409,
            detail={"code": policy["error_codes"]["condition_transition_conflict"]},
        )
    await audit(
        user.id,
        transition["event"],
        policy["condition_entity_type"],
        condition_id,
        condition["project_id"],
        {"from": condition["status"], "to": target, "note": payload.note},
    )
    return updated


async def resolve_finding(condition_id, finding_id, payload, user):
    policy = TEST_ANALYSIS_POLICY
    condition = await get_condition_for_user(
        condition_id, user, policy["permissions"]["resolve_finding"]
    )
    if condition["status"] == policy["archived_status"]:
        raise HTTPException(
            status_code=409,
            detail={
                "code": policy["error_codes"]["artifact_archived"],
                "artifact_type": policy["condition_artifact_type"],
            },
        )
    found = False
    findings = []
    for finding in condition.get("analysis_findings", []):
        if finding.get("finding_id") != finding_id:
            findings.append(finding)
            continue
        found = True
        if finding.get("status") != policy["open_status"]:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["error_codes"]["finding_already_resolved"]},
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
        raise HTTPException(
            status_code=404, detail={"code": policy["error_codes"]["finding_not_found"]}
        )
    updated = await test_condition_repository.update(
        condition_id,
        condition["project_id"],
        payload.expected_revision,
        set(policy["condition_mutable_finding_statuses"]),
        {"analysis_findings": findings, "updated_at": now()},
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["revision_conflict"]}
        )
    await audit(
        user.id,
        policy["events"]["finding_resolved"],
        policy["condition_entity_type"],
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
    policy = TEST_ANALYSIS_POLICY
    await get_project(project_id, user, policy["permissions"]["run_ai"])
    existing = await test_analysis_repository.find_ai_result(
        project_id, payload.idempotency_key
    )
    if existing:
        if existing.get("result_type") != policy["ai_result_type"]:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["error_codes"]["idempotency_reused"]},
            )
        return existing
    basis_snapshots = await resolve_basis(project_id, payload.basis_refs)
    evidence = [
        {
            "artifact_type": item["artifact_type"],
            "artifact_id": item["artifact_id"],
            "artifact_version_id": item.get("artifact_version_id") or item["resolved_id"],
            "authority": policy["basis_authority"],
            "text": item["text"],
        }
        for item in basis_snapshots
    ]
    instruction = json.dumps(
        {"user_instruction": payload.instruction},
        ensure_ascii=False,
    )
    ai_result = await request_design_assistance(
        "test_condition_generation", project_id, instruction, evidence
    )
    raw_candidates = [
        item
        for item in ai_result.get("suggestions", [])
        if isinstance(item, dict) and str(item.get("title") or "").strip()
    ]
    candidates = [
        {
            **item,
            "candidate_id": f"{policy['candidate_prefix']}{index}",
            "status": policy["candidate_status"],
            "candidate_only": True,
            "basis_refs": [ref.model_dump() for ref in payload.basis_refs],
        }
        for index, item in enumerate(raw_candidates, 1)
    ]
    value = {
        "_id": new_id(policy["ai_result_id_prefix"]),
        "project_id": project_id,
        "result_type": policy["ai_result_type"],
        "candidates": candidates,
        "basis_snapshots": basis_snapshots,
        "candidate_only": True,
        "human_confirmation_required": True,
        **ai_contract_metadata(ai_result),
        "idempotency_key": payload.idempotency_key,
        "created_by": user.id,
        "created_at": now(),
    }
    try:
        await test_analysis_repository.insert_ai_result(value)
    except DuplicateKeyError:
        return await test_analysis_repository.find_ai_result(
            project_id, payload.idempotency_key
        )
    await audit(
        user.id,
        policy["events"]["ai_generated"],
        policy["ai_result_entity_type"],
        value["_id"],
        project_id,
        {"candidate_count": len(candidates), "status": value["status"]},
    )
    return value


async def condition_coverage(project_id, user):
    policy = TEST_ANALYSIS_POLICY
    await get_project(project_id, user, policy["permissions"]["condition_read"])
    conditions = await test_analysis_repository.list_conditions(
        project_id, policy["archived_status"], policy["condition_limit"]
    )
    condition_ids = [item["_id"] for item in conditions]
    scenarios = await test_analysis_repository.list_scenarios(
        project_id, condition_ids, policy["scenario_limit"]
    )
    case_versions = await test_analysis_repository.list_case_versions(
        project_id,
        condition_ids,
        [item["_id"] for item in scenarios],
        policy["case_version_limit"],
    )
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


async def run_deterministic_analysis(project_id, payload, user):
    policy = TEST_ANALYSIS_POLICY
    await get_project(project_id, user, policy["permissions"]["execute"])
    snapshots = await resolve_basis(project_id, payload.basis_refs)
    findings = deterministic_testability_findings(snapshots)
    await audit(
        user.id,
        policy["events"]["analysis_executed"],
        policy["project_entity_type"],
        project_id,
        project_id,
        {
            "basis_count": len(snapshots),
            "finding_count": len(findings),
            "engine": policy["deterministic_engine"],
        },
    )
    return {
        "status": policy["success_status"],
        "engine": policy["deterministic_engine"],
        "findings": findings,
        "basis_snapshots": snapshots,
    }


async def list_analysis_findings(project_id, user, status="", limit=500):
    await get_project(
        project_id, user, TEST_ANALYSIS_POLICY["permissions"]["analysis_read"]
    )
    query = {"project_id": project_id}
    if status:
        query["status"] = status
    items = await test_analysis_repository.list_findings(query, limit)
    return {"items": items, "total": len(items)}


async def create_analysis_finding(project_id, payload, user):
    policy = TEST_ANALYSIS_POLICY
    await get_project(project_id, user, policy["permissions"]["finding_create"])
    ref_type = payload.artifact_type.upper()
    collection_name = BASIS_COLLECTIONS.get(ref_type)
    if not collection_name:
        raise HTTPException(
            status_code=422, detail={"code": policy["error_codes"]["basis_type_invalid"]}
        )
    identifier = payload.artifact_version_id or payload.artifact_id
    if not await test_analysis_repository.find_basis(
        collection_name, identifier, project_id
    ):
        raise HTTPException(
            status_code=422,
            detail={"code": policy["error_codes"]["cross_project_reference"]},
        )
    timestamp = now()
    value = {
        "_id": new_id(policy["finding_id_prefix"]),
        "project_id": project_id,
        **payload.model_dump(),
        "status": policy["open_status"],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await test_analysis_repository.insert_finding(value)
    await audit(
        user.id,
        policy["events"]["finding_created"],
        policy["finding_entity_type"],
        value["_id"],
        project_id,
        {"category": value["category"], "severity": value["severity"]},
    )
    return value


async def assign_analysis_finding(finding_id, payload, user):
    policy = TEST_ANALYSIS_POLICY
    finding = await test_analysis_repository.find_finding(finding_id)
    if not finding:
        raise HTTPException(
            status_code=404,
            detail={"code": policy["error_codes"]["analysis_finding_not_found"]},
        )
    await get_project(finding["project_id"], user, policy["permissions"]["finding_assign"])
    member = await test_analysis_repository.find_active_member(
        finding["project_id"], payload.owner_id, policy["active_member_status"]
    )
    if not member:
        raise HTTPException(
            status_code=422,
            detail={"code": policy["error_codes"]["project_member_not_found"]},
        )
    updated = await test_analysis_repository.update_finding(
        {
            "_id": finding_id,
            "revision": payload.expected_revision,
            "status": {"$in": policy["finding_active_statuses"]},
        },
        {
            "owner_id": payload.owner_id,
            "status": policy["in_progress_status"],
            "updated_at": now(),
        },
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["stale_revision"]}
        )
    await audit(
        user.id,
        policy["events"]["finding_assigned"],
        policy["finding_entity_type"],
        finding_id,
        finding["project_id"],
        {"owner_id": payload.owner_id},
    )
    return updated


async def transition_analysis_finding(finding_id, payload, user, verify=False):
    policy = TEST_ANALYSIS_POLICY
    finding = await test_analysis_repository.find_finding(finding_id)
    if not finding:
        raise HTTPException(
            status_code=404,
            detail={"code": policy["error_codes"]["analysis_finding_not_found"]},
        )
    permission = (
        policy["permissions"]["verify_finding"]
        if verify
        else policy["permissions"]["resolve_finding"]
    )
    await get_project(finding["project_id"], user, permission)
    if (verify and finding.get("status") != policy["resolved_status"]) or (
        not verify and finding.get("status") not in policy["finding_active_statuses"]
    ):
        if finding.get("status") in policy["finding_terminal_statuses"]:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["error_codes"]["finding_already_resolved"]},
            )
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["invalid_transition"]}
        )
    source = (
        policy["resolved_status"]
        if verify
        else {"$in": policy["finding_active_statuses"]}
    )
    target = policy["verified_status"] if verify else policy["resolved_status"]
    changes = {
        "status": target,
        "updated_at": now(),
        "resolution": payload.resolution,
        "resolution_ref": payload.resolution_ref,
    }
    changes["verified_by" if verify else "resolved_by"] = user.id
    changes["verified_at" if verify else "resolved_at"] = now()
    updated = await test_analysis_repository.update_finding(
        {"_id": finding_id, "revision": payload.expected_revision, "status": source},
        changes,
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["invalid_transition"]}
        )
    await audit(
        user.id,
        policy["events"]["analysis_finding_verified"]
        if verify
        else policy["events"]["analysis_finding_resolved"],
        policy["finding_entity_type"],
        finding_id,
        finding["project_id"],
        {},
    )
    return updated


async def review_condition(condition_id, payload, user):
    policy = TEST_ANALYSIS_POLICY
    condition = await get_condition_for_user(
        condition_id, user, policy["permissions"]["condition_review"]
    )
    updated = await test_condition_repository.update(
        condition_id,
        condition["project_id"],
        payload.expected_revision,
        {policy["review_status"]},
        {
            "reviewed_by": list(dict.fromkeys([*condition.get("reviewed_by", []), user.id])),
            "review_note": payload.note,
            "updated_at": now(),
        },
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["error_codes"]["stale_revision"]}
        )
    await audit(
        user.id,
        policy["events"]["condition_reviewed"],
        policy["condition_entity_type"],
        condition_id,
        condition["project_id"],
        {"note": payload.note},
    )
    return updated


async def bulk_prioritize_conditions(project_id, payload, user):
    policy = TEST_ANALYSIS_POLICY
    await get_project(project_id, user, policy["permissions"]["condition_bulk_update"])
    results = []
    for item in payload.items:
        condition = await test_condition_repository.get(item["condition_id"], project_id)
        if not condition:
            raise HTTPException(
                status_code=404,
                detail={"code": policy["error_codes"]["condition_not_found"]},
            )
        updated = await test_condition_repository.update(
            item["condition_id"],
            project_id,
            int(item["expected_revision"]),
            {policy["draft_status"]},
            {"priority": item["priority"], "updated_at": now()},
        )
        if not updated:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": policy["error_codes"]["stale_revision"],
                    "condition_id": item["condition_id"],
                },
            )
        results.append(updated)
        await audit(
            user.id,
            policy["events"]["condition_updated"],
            policy["condition_entity_type"],
            item["condition_id"],
            project_id,
            {"fields": ["priority"]},
        )
    return {"items": results, "total": len(results)}
