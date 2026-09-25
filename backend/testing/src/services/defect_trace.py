from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project_entity, new_id, now, optimistic_patch
from src.repositories.defect import defect_repository
from src.services.defect_analysis import build_defect_trace_candidates
from src.services.domain_policy import domain_policy


async def suggest_defect_trace_record(project_id, defect_id, payload, user):
    policy = domain_policy("defect")
    defect = await get_project_entity(
        policy["collection"], defect_id, user, policy["trace_suggest_permission"]
    )
    if defect["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
    existing = await defect_repository.find_ai_result_by_idempotency(
        project_id, payload.idempotency_key
    )
    if existing:
        if (
            existing.get("subject_id") != defect_id
            or existing.get("result_type") != policy["trace_result_type"]
        ):
            raise HTTPException(
                status_code=409, detail={"code": policy["idempotency_reused_code"]}
            )
        return existing
    requirement_candidates, test_case_candidates = await build_defect_trace_candidates(defect)
    result = {
        "_id": new_id(policy["ai_result_id_prefix"]),
        "project_id": project_id,
        "result_type": policy["trace_result_type"],
        "subject_type": policy["trace_subject_type"],
        "subject_id": defect_id,
        "status": policy["success_status"],
        "candidate_only": True,
        "human_confirmation_required": True,
        "requirement_candidates": requirement_candidates,
        "test_case_candidates": test_case_candidates,
        "model": policy["trace_model"],
        "idempotency_key": payload.idempotency_key,
        "review_status": policy["pending_review_status"],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": now(),
        "updated_at": now(),
    }
    try:
        await defect_repository.insert_ai_result(result)
    except DuplicateKeyError:
        existing = await defect_repository.find_ai_result_by_idempotency(
            project_id, payload.idempotency_key
        )
        if not existing:
            raise
        if (
            existing.get("subject_id") != defect_id
            or existing.get("result_type") != policy["trace_result_type"]
        ):
            raise HTTPException(
                status_code=409, detail={"code": policy["idempotency_reused_code"]}
            )
        return existing
    await audit(
        user.id,
        policy["trace_suggested_event"],
        policy["ai_result_entity"],
        result["_id"],
        project_id,
        {
            "defect_id": defect_id,
            "requirement_candidate_count": len(requirement_candidates),
            "test_case_candidate_count": len(test_case_candidates),
        },
    )
    return result


async def list_defect_trace_candidates(defect_id, user):
    policy = domain_policy("defect")
    defect = await get_project_entity(
        policy["collection"], defect_id, user, policy["trace_suggest_permission"]
    )
    _, test_case_candidates = await build_defect_trace_candidates(defect)
    return test_case_candidates


async def update_defect_trace_record(project_id, defect_id, payload, user):
    policy = domain_policy("defect")
    trace_policy = domain_policy("defect_trace")
    defect = await get_project_entity(
        policy["collection"],
        defect_id,
        user,
        policy["trace_manage_permission"],
        assigned_role=policy["developer_role"],
        assigned_user_field="assignee",
    )
    if defect["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
    changes = {}
    fields = payload.model_fields_set
    if "linked_test_result_id" in fields:
        if payload.linked_test_result_id:
            result = await defect_repository.find_test_result(
                payload.linked_test_result_id,
                project_id,
                policy["failed_result_status"],
            )
            if not result:
                raise HTTPException(
                    status_code=422, detail={"code": policy["failed_result_required_code"]}
                )
        changes["linked_test_result_id"] = payload.linked_test_result_id
    if "linked_test_case_version_id" in fields:
        if payload.linked_test_case_version_id:
            version = await defect_repository.find_test_case_version(
                payload.linked_test_case_version_id, project_id
            )
            if not version:
                raise HTTPException(
                    status_code=422, detail={"code": policy["invalid_test_version_code"]}
                )
        changes["linked_test_case_version_id"] = payload.linked_test_case_version_id
    if "linked_requirement_version_ids" in fields:
        requirement_ids = list(dict.fromkeys(payload.linked_requirement_version_ids or []))
        count = await defect_repository.count_requirement_versions(
            project_id, requirement_ids
        )
        if count != len(requirement_ids):
            raise HTTPException(
                status_code=422,
                detail={"code": policy["invalid_requirement_version_code"]},
            )
        changes["linked_requirement_version_ids"] = requirement_ids
    ai_result = None
    if payload.ai_result_id:
        ai_result = await defect_repository.find_ai_result(
            payload.ai_result_id,
            project_id,
            policy["trace_result_type"],
            defect_id,
        )
        if not ai_result:
            raise HTTPException(
                status_code=422, detail={"code": policy["invalid_ai_result_code"]}
            )
        candidates = ai_result.get("requirement_candidates", []) + ai_result.get(
            "test_case_candidates", []
        )
        candidate_ids = {item.get("candidate_id") for item in candidates}
        if (
            not payload.accepted_candidate_ids
            or not set(payload.accepted_candidate_ids) <= candidate_ids
        ):
            raise HTTPException(
                status_code=422, detail={"code": policy["invalid_ai_candidate_code"]}
            )
        accepted = {
            item["candidate_id"]: item
            for item in candidates
            if item.get("candidate_id") in payload.accepted_candidate_ids
        }
        accepted_requirements = {
            item["artifact_id"]
            for item in accepted.values()
            if item.get("artifact_type") == trace_policy["requirement_artifact_type"]
        }
        accepted_test_cases = {
            item["artifact_id"]
            for item in accepted.values()
            if item.get("artifact_type") == trace_policy["test_case_artifact_type"]
        }
        new_requirements = set(changes.get("linked_requirement_version_ids", [])) - set(
            defect.get("linked_requirement_version_ids", [])
        )
        selected_test_case = changes.get("linked_test_case_version_id")
        if not new_requirements <= accepted_requirements or (
            selected_test_case
            and selected_test_case != defect.get("linked_test_case_version_id")
            and selected_test_case not in accepted_test_cases
        ):
            raise HTTPException(
                status_code=422, detail={"code": policy["ai_candidate_mismatch_code"]}
            )
    updated = await optimistic_patch(
        policy["collection"], defect_id, project_id, payload.expected_revision, changes
    )
    if ai_result:
        timestamp = now()
        await defect_repository.review_ai_result(
            ai_result["_id"],
            project_id,
            {
                "review_status": policy["reviewed_status"],
                "accepted_candidate_ids": list(dict.fromkeys(payload.accepted_candidate_ids)),
                "review_reason": payload.reason,
                "reviewed_by": user.id,
                "reviewed_at": timestamp,
                "updated_at": timestamp,
            },
        )
    await audit(
        user.id,
        policy["trace_updated_event"],
        policy["entity"],
        defect_id,
        project_id,
        {
            "reason": payload.reason,
            "changed_fields": sorted(changes),
            "ai_result_id": payload.ai_result_id,
            "accepted_candidate_ids": payload.accepted_candidate_ids,
        },
    )
    return updated
