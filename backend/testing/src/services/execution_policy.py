import hashlib

from bson.json_util import dumps as bson_dumps
from fastapi import HTTPException

from src.repositories import execution_policy_repository
from src.services.domain_policy import domain_policy


EXECUTION_POLICY = domain_policy("execution")
FROZEN_RUN_SCOPE_FIELDS = tuple(EXECUTION_POLICY["frozen_run_scope_fields"])
DEFECT_TRANSITIONS = {
    status: set(targets)
    for status, targets in EXECUTION_POLICY["defect_transitions"].items()
}
EXECUTION_TRANSITIONS = {
    status: set(targets)
    for status, targets in EXECUTION_POLICY["result_transitions"].items()
}


def frozen_run_scope(run):
    return {field: run.get(field) for field in FROZEN_RUN_SCOPE_FIELDS}


def frozen_run_scope_hash(scope):
    canonical = bson_dumps(scope, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def enforce_not_applicable_policy(project_id, status, step_results=None):
    uses_not_applicable = status == EXECUTION_POLICY["not_applicable_status"] or any(
        item.status == EXECUTION_POLICY["not_applicable_status"] for item in step_results or []
    )
    if not uses_not_applicable:
        return
    project = await execution_policy_repository.project_settings(project_id)
    if not project or not (project.get("settings") or {}).get(
        EXECUTION_POLICY["not_applicable_setting"],
        EXECUTION_POLICY["not_applicable_setting_default"],
    ):
        raise HTTPException(
            status_code=409,
            detail={"code": EXECUTION_POLICY["not_applicable_disabled_code"]},
        )


async def select_resume_execution(run, user):
    version_ids = list(run.get("test_case_version_ids", []))
    membership = await execution_policy_repository.active_membership_role(
        run["project_id"], user.id, EXECUTION_POLICY["active_membership_status"]
    )
    assignments = run.get("test_case_assignments") or {}
    eligible_ids = version_ids
    assignment_mode = EXECUTION_POLICY["project_scope_mode"]
    if membership and membership.get("project_role") == EXECUTION_POLICY["tester_role"]:
        explicit_ids = [
            version_id for version_id in version_ids if assignments.get(version_id) == user.id
        ]
        if explicit_ids:
            eligible_ids = explicit_ids
            assignment_mode = EXECUTION_POLICY["case_assignment_mode"]
        elif run.get("assignee_id") == user.id:
            eligible_ids = [
                version_id for version_id in version_ids if version_id not in assignments
            ]
            assignment_mode = EXECUTION_POLICY["run_assignment_mode"]
        elif run.get("assignee_id") or assignments:
            raise HTTPException(
                status_code=403,
                detail={"code": EXECUTION_POLICY["assignment_required_code"]},
            )
    results = await execution_policy_repository.list_results(run["_id"], eligible_ids)
    by_version = {item["test_case_version_id"]: item for item in results}
    current_version_id = next(
        (
            version_id
            for version_id in eligible_ids
            if by_version.get(version_id, {}).get("status")
            == EXECUTION_POLICY["in_progress_status"]
        ),
        None,
    )
    if current_version_id is None:
        current_version_id = next(
            (
                version_id
                for version_id in eligible_ids
                if by_version.get(version_id, {}).get("status")
                == EXECUTION_POLICY["not_run_status"]
            ),
            None,
        )
    current_execution = by_version.get(current_version_id) if current_version_id else None
    current_version = (
        await execution_policy_repository.find_test_case_version(
            current_version_id, run["project_id"]
        )
        if current_version_id
        else None
    )
    return {
        "current_execution": current_execution,
        "current_test_case_version": current_version,
        "position": version_ids.index(current_version_id) + 1 if current_version_id else None,
        "total_count": len(version_ids),
        "remaining_count": sum(
            by_version.get(version_id, {}).get("status")
            in set(EXECUTION_POLICY["remaining_statuses"])
            for version_id in eligible_ids
        ),
        "assignment_mode": assignment_mode,
    }


async def replay_resume_event(run, event):
    execution = (
        await execution_policy_repository.find_result(event.get("current_execution_id"))
        if event.get("current_execution_id")
        else None
    )
    version = (
        await execution_policy_repository.find_test_case_version(
            event.get("current_test_case_version_id"), run["project_id"]
        )
        if event.get("current_test_case_version_id")
        else None
    )
    return {
        "run": run,
        "resume_event": event,
        "current_execution": execution,
        "current_test_case_version": version,
        "position": event.get("position"),
        "total_count": event.get("total_count", len(run.get("test_case_version_ids", []))),
        "remaining_count": event.get("remaining_count", 0),
        "assignment_mode": event.get(
            "assignment_mode", EXECUTION_POLICY["project_scope_mode"]
        ),
        "scope_fingerprint": event.get("scope_fingerprint"),
    }


async def validate_test_versions(project_id, version_ids):
    count = await execution_policy_repository.count_test_case_versions(
        project_id, version_ids
    )
    if count != len(set(version_ids)):
        raise HTTPException(
            status_code=422,
            detail={"code": EXECUTION_POLICY["missing_test_version_code"]},
        )
