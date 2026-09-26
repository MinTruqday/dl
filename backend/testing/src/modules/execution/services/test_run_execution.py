from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project_entity, new_id, now, plain_text
from src.repositories.test_run import test_run_repository
from src.services.domain_policy import domain_policy
from src.services.execution_policy import (
    EXECUTION_TRANSITIONS,
    enforce_not_applicable_policy,
    frozen_run_scope,
    frozen_run_scope_hash,
    replay_resume_event,
    select_resume_execution,
)
from src.clients.project_knowledge import index_artifact


TEST_RUN_POLICY = domain_policy("test_run")


async def start_test_run_record(run_id, user):
    policy = TEST_RUN_POLICY
    run = await get_project_entity(
        policy["run_collection"], run_id, user, policy["start_permission"]
    )
    if run["status"] == policy["in_progress_status"]:
        return run
    if run["status"] not in policy["startable_statuses"]:
        raise HTTPException(status_code=409, detail={"code": policy["invalid_transition_code"]})
    if run.get("environment_id"):
        environment = await test_run_repository.find_environment(
            run["environment_id"], run["project_id"]
        )
        if environment and environment.get("availability") != policy["available_environment_status"]:
            raise HTTPException(
                status_code=409,
                detail={"code": policy["environment_unavailable_code"]},
            )
    scope = frozen_run_scope(run)
    scope_fingerprint = frozen_run_scope_hash(scope)
    timestamp = now()
    updated = await test_run_repository.transition_run(
        {"_id": run_id, "status": run["status"], "revision": run.get("revision", 1)},
        {
            "status": policy["in_progress_status"],
            "frozen_scope": scope,
            "frozen_scope_hash": scope_fingerprint,
            "started_at": timestamp,
            "started_by": user.id,
            "updated_at": timestamp,
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(user.id, policy["started_event"], policy["run_entity"], run_id, run["project_id"])
    return updated


async def resume_test_run_record(project_id, run_id, payload, user):
    policy = TEST_RUN_POLICY
    run = await get_project_entity(
        policy["run_collection"], run_id, user, policy["execute_permission"]
    )
    if run["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
    existing = await test_run_repository.find_resume_event(run_id, payload.idempotency_key)
    if existing:
        return await replay_resume_event(run, existing), run.get("revision", 1)
    if run.get("status") != policy["in_progress_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["not_in_progress_code"]})
    if run.get("revision", 1) != payload.expected_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": policy["revision_conflict_code"],
                "current_revision": run.get("revision", 1),
            },
        )
    scope = frozen_run_scope(run)
    scope_fingerprint = frozen_run_scope_hash(scope)
    if run.get("frozen_scope_hash") and run["frozen_scope_hash"] != scope_fingerprint:
        raise HTTPException(status_code=409, detail={"code": policy["scope_changed_code"]})
    selected = await select_resume_execution(run, user)
    timestamp = now()
    event = {
        "_id": new_id(policy["resume_id_prefix"]),
        "project_id": project_id,
        "test_run_id": run_id,
        "idempotency_key": payload.idempotency_key,
        "scope_fingerprint": scope_fingerprint,
        "current_execution_id": (
            selected["current_execution"]["_id"] if selected["current_execution"] else None
        ),
        "current_test_case_version_id": (
            selected["current_test_case_version"]["_id"]
            if selected["current_test_case_version"]
            else None
        ),
        "position": selected["position"],
        "total_count": selected["total_count"],
        "remaining_count": selected["remaining_count"],
        "assignment_mode": selected["assignment_mode"],
        "resumed_by": user.id,
        "created_at": timestamp,
    }
    try:
        await test_run_repository.insert_resume_event(event)
    except DuplicateKeyError:
        existing = await test_run_repository.find_resume_event(run_id, payload.idempotency_key)
        return await replay_resume_event(run, existing), run.get("revision", 1)
    updated = await test_run_repository.transition_run(
        {
            "_id": run_id,
            "project_id": project_id,
            "status": policy["in_progress_status"],
            "revision": payload.expected_revision,
        },
        {
            "frozen_scope": run.get("frozen_scope") or scope,
            "frozen_scope_hash": scope_fingerprint,
            "last_resumed_at": timestamp,
            "last_resumed_by": user.id,
            "last_resume_event_id": event["_id"],
            "updated_at": timestamp,
        },
    )
    if not updated:
        await test_run_repository.delete_resume_event(event["_id"])
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await test_run_repository.set_resume_event_revision(event["_id"], updated["revision"])
    event["run_revision"] = updated["revision"]
    await audit(
        user.id,
        policy["resumed_event"],
        policy["run_entity"],
        run_id,
        project_id,
        {
            "resume_event_id": event["_id"],
            "current_test_case_version_id": event["current_test_case_version_id"],
            "scope_fingerprint": scope_fingerprint,
        },
    )
    return (
        {"run": updated, "resume_event": event, **selected, "scope_fingerprint": scope_fingerprint},
        updated["revision"],
    )


async def record_test_result_entry(run_id, test_case_version_id, payload, user):
    policy = TEST_RUN_POLICY
    run = await get_project_entity(
        policy["run_collection"], run_id, user, policy["execute_permission"]
    )
    if run["status"] != policy["in_progress_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["not_in_progress_code"]})
    if run.get("execution_paused"):
        raise HTTPException(
            status_code=409,
            detail={
                "code": policy["paused_by_incident_code"],
                "incident_id": run.get("paused_by_environment_incident_id"),
            },
        )
    if test_case_version_id not in run["test_case_version_ids"]:
        raise HTTPException(status_code=422, detail={"code": policy["test_not_in_snapshot_code"]})
    existing = await test_run_repository.find_result_for_case(run_id, test_case_version_id)
    if existing and existing.get("idempotency_key") == payload.idempotency_key:
        return existing
    await enforce_not_applicable_policy(run["project_id"], payload.status, payload.step_results)
    if existing:
        if existing.get("status") != policy["not_run_status"]:
            raise HTTPException(status_code=409, detail={"code": policy["result_already_recorded_code"]})
        timestamp = now()
        result = await test_run_repository.update_result(
            {
                "_id": existing["_id"],
                "project_id": run["project_id"],
                "status": policy["not_run_status"],
                "revision": existing.get("revision", 1),
            },
            {
                **payload.model_dump(),
                "executor_id": user.id,
                "executed_by": user.id,
                "started_at": existing.get("started_at") or timestamp,
                "completed_at": timestamp,
                "executed_at": timestamp,
                "updated_at": timestamp,
            },
        )
        if not result:
            raise HTTPException(status_code=409, detail={"code": policy["execution_conflict_code"]})
    else:
        timestamp = now()
        result = {
            "_id": new_id(policy["result_id_prefix"]),
            "project_id": run["project_id"],
            "test_run_id": run_id,
            "test_case_version_id": test_case_version_id,
            "environment": run.get("environment"),
            "build": run.get("build"),
            **payload.model_dump(),
            "revision": 1,
            "executor_id": user.id,
            "executed_by": user.id,
            "started_at": timestamp,
            "completed_at": timestamp,
            "executed_at": timestamp,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        await test_run_repository.insert_result(result)
    await test_run_repository.touch_run(run_id, None, now())
    await audit(
        user.id,
        policy["result_recorded_event"],
        policy["result_entity"],
        result["_id"],
        run["project_id"],
        {"status": payload.status},
    )
    await index_artifact(
        run["project_id"],
        policy["result_artifact_type"],
        result["_id"],
        result["_id"],
        result["_id"],
        " ".join(
            [
                str(result.get("status") or ""),
                plain_text(result.get("actual_result_doc", {})),
                str(result.get("note") or ""),
            ]
        ),
        result["status"],
        policy["project_reference_authority"],
        result.get("revision", 1),
        test_run_id=run_id,
        test_case_version_id=test_case_version_id,
    )
    return result


async def update_test_execution_record(project_id, execution_id, payload, user):
    policy = TEST_RUN_POLICY
    result = await get_project_entity(
        policy["result_collection"], execution_id, user, policy["execute_permission"]
    )
    if result["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
    existing_event = await test_run_repository.find_execution_update(
        execution_id, payload.idempotency_key
    )
    if existing_event:
        return {
            "execution": await test_run_repository.find_result(execution_id),
            "update": existing_event,
        }
    await enforce_not_applicable_policy(project_id, payload.status, payload.step_results)
    run = await test_run_repository.find_run(result["test_run_id"], project_id)
    if not run or run.get("status") != policy["in_progress_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["not_in_progress_code"]})
    if run.get("execution_paused"):
        raise HTTPException(
            status_code=409,
            detail={
                "code": policy["paused_by_incident_code"],
                "incident_id": run.get("paused_by_environment_incident_id"),
            },
        )
    allowed = EXECUTION_TRANSITIONS.get(result.get("status"), set())
    if payload.status not in allowed:
        raise HTTPException(
            status_code=409,
            detail={
                "code": policy["invalid_execution_transition_code"],
                "from": result.get("status"),
                "to": payload.status,
            },
        )
    expected_revision = payload.expected_revision or result.get("revision", 1)
    timestamp = now()
    terminal = payload.status in policy["terminal_result_statuses"]
    updated = await test_run_repository.update_result(
        {"_id": execution_id, "project_id": project_id, "revision": expected_revision},
        {
            "status": payload.status,
            "step_results": [item.model_dump() for item in payload.step_results],
            "actual_result_doc": payload.actual_result_doc,
            "attachments": payload.attachments,
            "note": payload.note,
            "executor_id": user.id,
            "executed_by": user.id,
            "started_at": result.get("started_at") or timestamp,
            "completed_at": timestamp if terminal else None,
            "executed_at": timestamp if terminal else result.get("executed_at"),
            "updated_at": timestamp,
            "last_updated_by": user.id,
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    event = {
        "_id": new_id(policy["execution_update_id_prefix"]),
        "project_id": project_id,
        "test_result_id": execution_id,
        "from_status": result.get("status"),
        "to_status": payload.status,
        "idempotency_key": payload.idempotency_key,
        "updated_by": user.id,
        "created_at": now(),
    }
    try:
        await test_run_repository.insert_execution_update(event)
    except DuplicateKeyError:
        event = await test_run_repository.find_execution_update(
            execution_id, payload.idempotency_key
        )
    await test_run_repository.touch_run(result["test_run_id"], project_id, now())
    await audit(
        user.id,
        policy["execution_updated_event"],
        policy["execution_entity"],
        execution_id,
        project_id,
        {"status": payload.status},
    )
    return {"execution": updated, "update": event}


async def correct_test_result_record(result_id, payload, user):
    policy = TEST_RUN_POLICY
    result = await get_project_entity(
        policy["result_collection"], result_id, user, policy["correct_permission"]
    )
    existing = await test_run_repository.find_correction(result_id, payload.idempotency_key)
    if existing:
        return {
            "result": await test_run_repository.find_result(result_id),
            "correction": existing,
        }
    await enforce_not_applicable_policy(result["project_id"], payload.status)
    event = {
        "_id": new_id(policy["correction_id_prefix"]),
        "project_id": result["project_id"],
        "test_result_id": result_id,
        "from_status": result.get("status"),
        "to_status": payload.status,
        "reason": payload.reason,
        "idempotency_key": payload.idempotency_key,
        "corrected_by": user.id,
        "created_at": now(),
    }
    try:
        await test_run_repository.insert_correction(event)
    except DuplicateKeyError:
        event = await test_run_repository.find_correction(result_id, payload.idempotency_key)
        return {
            "result": await test_run_repository.find_result(result_id),
            "correction": event,
        }
    timestamp = now()
    await test_run_repository.update_result(
        {"_id": result_id},
        {
            "status": payload.status,
            "corrected": True,
            "last_correction_id": event["_id"],
            "completed_at": timestamp,
            "updated_at": timestamp,
        },
        {"correction_event_ids": event["_id"]},
    )
    await audit(
        user.id,
        policy["result_corrected_event"],
        policy["result_entity"],
        result_id,
        result["project_id"],
        {"from": result.get("status"), "to": payload.status, "correction_id": event["_id"]},
    )
    return {
        "result": await test_run_repository.find_result(result_id),
        "correction": event,
    }


async def complete_test_run_record(run_id, user):
    policy = TEST_RUN_POLICY
    run = await get_project_entity(
        policy["run_collection"], run_id, user, policy["complete_permission"]
    )
    if run["status"] == policy["completed_status"]:
        return run
    if run["status"] != policy["in_progress_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["invalid_transition_code"]})
    result_count = await test_run_repository.count_results_by_status(
        run_id, policy["terminal_result_statuses"]
    )
    total_count = len(run["test_case_version_ids"])
    project = await test_run_repository.project_settings(run["project_id"])
    partial_allowed = bool(
        (project.get("settings") or {}).get(
            policy["partial_completion_setting"], policy["default_partial_completion"]
        )
    )
    if result_count < total_count and not partial_allowed:
        raise HTTPException(
            status_code=409,
            detail={
                "code": policy["partial_execution_code"],
                "completed": result_count,
                "total": total_count,
            },
        )
    partial_completion = result_count < total_count
    timestamp = now()
    updated = await test_run_repository.update_run(
        run_id,
        {
            "status": policy["completed_status"],
            "completed_at": timestamp,
            "completed_by": user.id,
            "completed_result_count": result_count,
            "total_result_count": total_count,
            "partial_completion": partial_completion,
            "updated_at": timestamp,
        },
    )
    await audit(
        user.id,
        policy["completed_event"],
        policy["run_entity"],
        run_id,
        run["project_id"],
        {"completed": result_count, "total": total_count, "partial_completion": partial_completion},
    )
    return updated


async def abort_test_run_record(run_id, reason, user):
    policy = TEST_RUN_POLICY
    run = await get_project_entity(
        policy["run_collection"], run_id, user, policy["abort_permission"]
    )
    if run["status"] not in policy["abortable_statuses"]:
        raise HTTPException(status_code=409, detail={"code": policy["invalid_transition_code"]})
    timestamp = now()
    updated = await test_run_repository.update_run(
        run_id,
        {
            "status": policy["aborted_status"],
            "abort_reason": reason,
            "aborted_by": user.id,
            "aborted_at": timestamp,
            "updated_at": timestamp,
        },
    )
    await audit(
        user.id,
        policy["aborted_event"],
        policy["run_entity"],
        run_id,
        run["project_id"],
        {"reason": reason},
    )
    return updated
