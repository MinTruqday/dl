from fastapi import HTTPException

from src.core.common import (
    audit,
    get_project,
    get_project_entity,
    new_id,
    now,
    optimistic_patch,
)
from src.repositories.test_run import test_run_repository
from src.services.domain_policy import domain_policy
from src.services.execution_context import resolve_execution_context
from src.services.execution_policy import validate_test_versions
from src.clients.project_knowledge import index_artifact
from src.services.test_run_execution import (
    abort_test_run_record,
    complete_test_run_record,
    correct_test_result_record,
    record_test_result_entry,
    resume_test_run_record,
    start_test_run_record,
    update_test_execution_record,
)
from src.services.test_run_query import (
    build_test_run_report,
    get_test_run_record,
    list_test_result_records,
    list_test_run_records,
)


TEST_RUN_POLICY = domain_policy("test_run")

__all__ = [
    "abort_test_run_record",
    "build_test_run_report",
    "complete_test_run_record",
    "correct_test_result_record",
    "get_test_run_record",
    "list_test_result_records",
    "list_test_run_records",
    "record_test_result_entry",
    "resume_test_run_record",
    "start_test_run_record",
    "update_test_execution_record",
]


async def create_test_run_record(payload, project_id, user):
    policy = TEST_RUN_POLICY
    if project_id is not None and payload.project_id != project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
    await get_project(payload.project_id, user, policy["create_permission"])
    plan = None
    if payload.test_plan_id:
        plan = await test_run_repository.find_plan(payload.test_plan_id, payload.project_id)
        if not plan:
            raise HTTPException(status_code=422, detail={"code": policy["invalid_plan_code"]})
    context = await resolve_execution_context(
        payload.project_id,
        user,
        release_id=payload.release_id,
        build_id=payload.build_id,
        environment_id=payload.environment_id,
        release=payload.release,
        build=payload.build,
        environment=payload.environment,
    )
    version_ids = list(dict.fromkeys(payload.test_case_version_ids))
    if payload.test_suite_ids:
        suites = await test_run_repository.list_suites(
            payload.project_id, payload.test_suite_ids, policy["suite_lookup_limit"]
        )
        if len(suites) != len(set(payload.test_suite_ids)):
            raise HTTPException(status_code=422, detail={"code": policy["invalid_suite_code"]})
        for suite in suites:
            version_ids.extend(suite.get("test_case_version_ids", []))
        version_ids = list(dict.fromkeys(version_ids))
    await validate_test_versions(payload.project_id, version_ids)
    timestamp = now()
    device_scope = (
        {
            "device_matrix_id": plan.get("device_matrix_id"),
            "device_profile_keys": plan.get("device_profile_keys", []),
            "device_matrix_snapshot": plan.get("device_matrix_snapshot"),
        }
        if plan and plan.get("device_matrix_id")
        else {}
    )
    run = {
        "_id": new_id(policy["run_id_prefix"]),
        **payload.model_dump(),
        **context,
        **device_scope,
        "test_case_version_ids": version_ids,
        "status": policy["draft_status"],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await test_run_repository.insert_run(run)
    if version_ids:
        try:
            await test_run_repository.insert_results(
                [
                    {
                        "_id": new_id(policy["result_id_prefix"]),
                        "project_id": payload.project_id,
                        "test_run_id": run["_id"],
                        "test_case_version_id": version_id,
                        "environment": context["environment"],
                        "environment_id": context["environment_id"],
                        "release": context["release"],
                        "release_id": context["release_id"],
                        "build": context["build"],
                        "build_id": context["build_id"],
                        "status": policy["not_run_status"],
                        "step_results": [],
                        "actual_result_doc": {"type": "doc", "content": []},
                        "attachments": [],
                        "note": "",
                        "idempotency_key": None,
                        "revision": policy["initial_revision"],
                        "executor_id": None,
                        "started_at": None,
                        "completed_at": None,
                        "created_at": timestamp,
                        "updated_at": timestamp,
                    }
                    for version_id in version_ids
                ]
            )
        except Exception:
            await test_run_repository.delete_run_results(run["_id"], payload.project_id)
            await test_run_repository.delete_run(run["_id"], payload.project_id)
            raise
    await audit(
        user.id,
        policy["created_event"],
        policy["run_entity"],
        run["_id"],
        payload.project_id,
        {"test_count": len(version_ids)},
    )
    await index_artifact(
        payload.project_id,
        policy["execution_artifact_type"],
        run["_id"],
        run["_id"],
        run.get("name") or run["_id"],
        " ".join([run.get("name") or run["_id"], run.get("build") or ""]),
        run["status"],
        policy["project_reference_authority"],
        run["revision"],
        test_case_version_ids=version_ids,
    )
    return run


async def update_test_run_record(project_id, run_id, payload, user):
    policy = TEST_RUN_POLICY
    run = await get_project_entity(policy["run_collection"], run_id, user, policy["update_permission"])
    if run["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
    if run.get("status") != policy["draft_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["scope_frozen_code"]})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    version_ids = changes.get("test_case_version_ids", run.get("test_case_version_ids", []))
    if "test_suite_ids" in changes:
        suites = await test_run_repository.list_suites(
            project_id, changes["test_suite_ids"], policy["suite_lookup_limit"]
        )
        if len(suites) != len(set(changes["test_suite_ids"])):
            raise HTTPException(status_code=422, detail={"code": policy["invalid_suite_code"]})
        version_ids = list(
            dict.fromkeys(
                [
                    *version_ids,
                    *[item for suite in suites for item in suite.get("test_case_version_ids", [])],
                ]
            )
        )
        changes["test_case_version_ids"] = version_ids
    if "test_case_version_ids" in changes:
        await validate_test_versions(project_id, version_ids)
    if {"release_id", "build_id", "environment_id", "release", "build", "environment"} & set(
        changes
    ):
        changes.update(
            await resolve_execution_context(
                project_id,
                user,
                release_id=changes.get("release_id", run.get("release_id")),
                build_id=changes.get("build_id", run.get("build_id")),
                environment_id=changes.get("environment_id", run.get("environment_id")),
                release=changes.get("release", run.get("release", "")),
                build=changes.get("build", run.get("build", "")),
                environment=changes.get("environment", run.get("environment", "")),
            )
        )
    updated = await optimistic_patch(
        policy["run_collection"], run_id, project_id, payload.expected_revision, changes
    )
    await audit(user.id, policy["updated_event"], policy["run_entity"], run_id, project_id)
    return updated


async def assign_test_run_record(project_id, run_id, payload, user):
    policy = TEST_RUN_POLICY
    run = await get_project_entity(policy["run_collection"], run_id, user, policy["assign_permission"])
    if run["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
    if payload.assignee_id:
        assignee = await test_run_repository.find_active_tester(
            project_id,
            payload.assignee_id,
            policy["active_member_status"],
            policy["tester_role"],
        )
        if not assignee:
            raise HTTPException(
                status_code=422,
                detail={"code": policy["invalid_assignee_code"], "user_id": payload.assignee_id},
            )
    assigned_users = set(payload.test_case_assignments.values())
    if assigned_users:
        valid_members = await test_run_repository.count_active_testers(
            project_id,
            list(assigned_users),
            policy["active_member_status"],
            policy["tester_role"],
        )
        if valid_members != len(assigned_users):
            raise HTTPException(status_code=422, detail={"code": policy["invalid_case_assignee_code"]})
    unknown = set(payload.test_case_assignments) - set(run.get("test_case_version_ids", []))
    if unknown:
        raise HTTPException(
            status_code=422,
            detail={"code": policy["test_not_in_snapshot_code"], "test_case_version_ids": sorted(unknown)},
        )
    updated = await optimistic_patch(
        policy["run_collection"],
        run_id,
        project_id,
        payload.expected_revision,
        {
            "assignee_id": payload.assignee_id,
            "test_case_assignments": payload.test_case_assignments,
        },
    )
    await audit(
        user.id,
        policy["assigned_event"],
        policy["run_entity"],
        run_id,
        project_id,
        {"assignee_id": payload.assignee_id},
    )
    return updated
