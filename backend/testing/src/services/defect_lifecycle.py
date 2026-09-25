from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import (
    audit,
    get_project,
    get_project_entity,
    new_id,
    now,
    optimistic_patch,
    require_action_policy,
)
from src.repositories.defect import defect_repository
from src.services.domain_policy import domain_policy
from src.services.execution_context import resolve_execution_context
from src.services.execution_policy import DEFECT_TRANSITIONS


DEFECT_POLICY = domain_policy("defect")


async def update_defect_record(defect_id, payload, project_id, user):
    policy = DEFECT_POLICY
    defect = await get_project_entity(
        policy["collection"],
        defect_id,
        user,
        policy["update_permission"],
        assigned_role=policy["developer_role"],
        assigned_user_field="assignee",
    )
    if project_id is not None and defect["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
    expected_revision = payload.get("expected_revision")
    if not isinstance(expected_revision, int):
        raise HTTPException(status_code=422, detail={"code": policy["missing_revision_code"]})
    if (
        "root_cause_category" in payload
        and payload["root_cause_category"] not in policy["root_cause_categories"]
    ):
        raise HTTPException(status_code=422, detail={"code": policy["invalid_root_cause_code"]})
    if "assignee" in payload:
        await get_project(defect["project_id"], user, policy["assign_permission"])
    if any(
        field in payload
        for field in {
            "linked_test_result_id",
            "linked_test_case_version_id",
            "linked_requirement_version_ids",
        }
    ):
        await get_project(
            defect["project_id"],
            user,
            policy["trace_manage_permission"],
            assigned_role=policy["developer_role"],
            assigned_user_id=defect.get("assignee"),
        )
    if "attachments" in payload:
        await get_project(
            defect["project_id"],
            user,
            policy["attachment_manage_permission"],
            assigned_role=policy["developer_role"],
            assigned_user_id=defect.get("assignee"),
        )
    if "linked_test_result_id" in payload and payload["linked_test_result_id"]:
        result = await defect_repository.find_test_result(
            payload["linked_test_result_id"], defect["project_id"]
        )
        if not result or result.get("status") != policy["failed_result_status"]:
            raise HTTPException(status_code=422, detail={"code": policy["failed_result_required_code"]})
    if "linked_test_case_version_id" in payload and payload["linked_test_case_version_id"]:
        version = await defect_repository.find_test_case_version(
            payload["linked_test_case_version_id"], defect["project_id"]
        )
        if not version:
            raise HTTPException(status_code=422, detail={"code": policy["invalid_test_version_code"]})
    if "linked_requirement_version_ids" in payload:
        requirement_ids = list(dict.fromkeys(payload.get("linked_requirement_version_ids") or []))
        count = await defect_repository.count_requirement_versions(
            defect["project_id"], requirement_ids
        )
        if count != len(requirement_ids):
            raise HTTPException(status_code=422, detail={"code": policy["invalid_requirement_version_code"]})
    changes = {key: value for key, value in payload.items() if key in policy["update_fields"]}
    if {"release_id", "build_id", "environment_id", "release", "build", "environment"} & set(
        changes
    ):
        changes.update(
            await resolve_execution_context(
                defect["project_id"],
                user,
                release_id=changes.get("release_id", defect.get("release_id")),
                build_id=changes.get("build_id", defect.get("build_id")),
                environment_id=changes.get("environment_id", defect.get("environment_id")),
                release=changes.get("release", defect.get("release", "")),
                build=changes.get("build", defect.get("build", "")),
                environment=changes.get("environment", defect.get("environment", "")),
            )
        )
    updated = await optimistic_patch(
        policy["collection"], defect_id, defect["project_id"], expected_revision, changes
    )
    await audit(user.id, policy["updated_event"], policy["entity"], defect_id, defect["project_id"])
    return updated


async def transition_defect_record(defect_id, payload, user):
    policy = DEFECT_POLICY
    permission = policy["transition_permissions"].get(
        payload.to_status, policy["default_transition_permission"]
    )
    defect = await get_project_entity(
        policy["collection"],
        defect_id,
        user,
        permission,
        assigned_role=policy["developer_role"]
        if permission == policy["developer_transition_permission"]
        else None,
        assigned_user_field="assignee"
        if permission == policy["developer_transition_permission"]
        else None,
    )
    if payload.to_status in policy["restricted_transition_statuses"]:
        await require_action_policy(
            defect["project_id"],
            user,
            f"defect.{payload.to_status.lower()}",
            set(policy["restricted_transition_roles"]),
        )
    allowed = DEFECT_TRANSITIONS.get(defect["status"], set())
    if payload.to_status not in allowed:
        raise HTTPException(
            status_code=409,
            detail={
                "code": policy["invalid_transition_code"],
                "from": defect["status"],
                "to": payload.to_status,
            },
        )
    updated = await defect_repository.transition_defect(
        defect_id,
        defect["project_id"],
        defect["status"],
        payload.expected_revision,
        {
            "status": payload.to_status,
            "transition_reason": payload.reason,
            "transitioned_by": user.id,
            "updated_at": now(),
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["transitioned_event"],
        policy["entity"],
        defect_id,
        defect["project_id"],
        {"from": defect["status"], "to": payload.to_status, "reason": payload.reason},
    )
    return updated


async def retest_defect_record(project_id, defect_id, payload, user):
    policy = DEFECT_POLICY
    defect = await get_project_entity(policy["collection"], defect_id, user, policy["retest_permission"])
    if defect["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
    existing = await defect_repository.find_retest(defect_id, payload.idempotency_key)
    if existing:
        return {
            "defect": await defect_repository.find_defect(defect_id, project_id),
            "retest": existing,
        }
    if defect["status"] != policy["ready_for_retest_status"]:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["not_ready_for_retest_code"], "status": defect["status"]},
        )
    result = await defect_repository.find_test_result(payload.test_result_id, project_id)
    if not result:
        raise HTTPException(status_code=422, detail={"code": policy["invalid_retest_result_code"]})
    if result.get("status") not in policy["retest_result_statuses"]:
        raise HTTPException(status_code=422, detail={"code": policy["retest_result_status_code"]})
    linked_version_id = defect.get("linked_test_case_version_id")
    if linked_version_id and result.get("test_case_version_id") != linked_version_id:
        raise HTTPException(status_code=422, detail={"code": policy["retest_version_mismatch_code"]})
    target_status = policy["retest_target_statuses"][result["status"]]
    event = {
        "_id": new_id(policy["retest_id_prefix"]),
        "project_id": project_id,
        "defect_id": defect_id,
        "test_result_id": result["_id"],
        "test_run_id": result["test_run_id"],
        "test_case_version_id": result["test_case_version_id"],
        "outcome": result["status"],
        "from_status": defect["status"],
        "to_status": target_status,
        "note": payload.note,
        "idempotency_key": payload.idempotency_key,
        "retested_by": user.id,
        "application_status": policy["pending_application_status"],
        "created_at": now(),
    }
    try:
        await defect_repository.insert_retest(event)
    except DuplicateKeyError:
        existing = await defect_repository.find_retest(defect_id, payload.idempotency_key)
        return {
            "defect": await defect_repository.find_defect(defect_id, project_id),
            "retest": existing,
        }
    updated = await defect_repository.apply_retest(
        defect_id,
        project_id,
        policy["ready_for_retest_status"],
        payload.expected_revision,
        target_status,
        event["_id"],
        result["_id"],
        now(),
    )
    if not updated:
        await defect_repository.delete_retest(
            event["_id"], policy["pending_application_status"]
        )
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    event["application_status"] = policy["applied_application_status"]
    await defect_repository.mark_retest_applied(
        event["_id"], policy["applied_application_status"]
    )
    await audit(
        user.id,
        policy["retested_event"],
        policy["entity"],
        defect_id,
        project_id,
        {"test_result_id": result["_id"], "outcome": result["status"], "to": target_status},
    )
    return {"defect": updated, "retest": event}
