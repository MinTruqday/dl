import csv
import hashlib
import io
import re
from difflib import SequenceMatcher

from bson.json_util import dumps as bson_dumps
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, next_key, now, optimistic_patch, page_payload, plain_text, require_action_policy, sort_spec
from src.core.database import database
from src.domain.schemas import (
    BugTraceSuggestionInput,
    DefectCreate,
    DefectRetestInput,
    DefectTraceUpdateInput,
    DefectTransition,
    TestExecutionPatch,
    TestPlanCreate,
    TestPlanPatch,
    TestResultCorrectionInput,
    TestResultInput,
    TestRunCreate,
    TestRunAssignmentInput,
    TestRunPatch,
    TestRunResumeInput,
    TestSuiteCreate,
    TestSuitePatch,
    ProjectArchiveInput,
    ReviewTransitionInput,
)
from src.services.project_knowledge import index_artifact
from src.services.execution_context import resolve_execution_context


router = APIRouter(prefix="/kiem-thu", tags=["Thực thi kiểm thử"])


FROZEN_RUN_SCOPE_FIELDS = (
    "test_plan_id",
    "test_suite_ids",
    "test_case_version_ids",
    "environment",
    "environment_id",
    "release",
    "release_id",
    "build",
    "build_id",
    "device_matrix_id",
    "device_profile_keys",
    "device_matrix_snapshot",
)


def frozen_run_scope(run):
    return {field: run.get(field) for field in FROZEN_RUN_SCOPE_FIELDS}


def frozen_run_scope_hash(scope):
    canonical = bson_dumps(scope, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def enforce_not_applicable_policy(project_id, status, step_results=None):
    uses_not_applicable = status == "NOT_APPLICABLE" or any(
        item.status == "NOT_APPLICABLE" for item in step_results or []
    )
    if not uses_not_applicable:
        return
    project = await database.value.projects.find_one({"_id": project_id}, {"settings": 1})
    if not project or not (project.get("settings") or {}).get(
        "allow_not_applicable_results", False
    ):
        raise HTTPException(
            status_code=409,
            detail={"code": "NOT_APPLICABLE_POLICY_DISABLED"},
        )


async def select_resume_execution(run, user):
    version_ids = list(run.get("test_case_version_ids", []))
    membership = await database.value.project_members.find_one(
        {"project_id": run["project_id"], "user_id": user.id, "status": "ACTIVE"},
        {"project_role": 1},
    )
    assignments = run.get("test_case_assignments") or {}
    eligible_ids = version_ids
    assignment_mode = "PROJECT_SCOPE"
    if membership and membership.get("project_role") == "TESTER":
        explicit_ids = [
            version_id for version_id in version_ids if assignments.get(version_id) == user.id
        ]
        if explicit_ids:
            eligible_ids = explicit_ids
            assignment_mode = "CASE_ASSIGNMENT"
        elif run.get("assignee_id") == user.id:
            eligible_ids = [version_id for version_id in version_ids if version_id not in assignments]
            assignment_mode = "RUN_ASSIGNMENT"
        elif run.get("assignee_id") or assignments:
            raise HTTPException(status_code=403, detail={"code": "TEST_RUN_ASSIGNMENT_REQUIRED"})
    results = await database.value.test_results.find(
        {"test_run_id": run["_id"], "test_case_version_id": {"$in": eligible_ids}}
    ).to_list(10000)
    by_version = {item["test_case_version_id"]: item for item in results}
    current_version_id = next(
        (
            version_id
            for version_id in eligible_ids
            if by_version.get(version_id, {}).get("status") == "IN_PROGRESS"
        ),
        None,
    )
    if current_version_id is None:
        current_version_id = next(
            (
                version_id
                for version_id in eligible_ids
                if by_version.get(version_id, {}).get("status") == "NOT_RUN"
            ),
            None,
        )
    current_execution = by_version.get(current_version_id) if current_version_id else None
    current_version = (
        await database.value.test_case_versions.find_one(
            {"_id": current_version_id, "project_id": run["project_id"]}
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
            by_version.get(version_id, {}).get("status") in {"NOT_RUN", "IN_PROGRESS"}
            for version_id in eligible_ids
        ),
        "assignment_mode": assignment_mode,
    }


async def replay_resume_event(run, event):
    execution = (
        await database.value.test_results.find_one({"_id": event.get("current_execution_id")})
        if event.get("current_execution_id")
        else None
    )
    version = (
        await database.value.test_case_versions.find_one(
            {"_id": event.get("current_test_case_version_id"), "project_id": run["project_id"]}
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
        "assignment_mode": event.get("assignment_mode", "PROJECT_SCOPE"),
        "scope_fingerprint": event.get("scope_fingerprint"),
    }


@router.post("/ke-hoach-kiem-thu", status_code=201)
@router.post("/du-an/{project_id}/ke-hoach-kiem-thu", status_code=201)
async def create_test_plan(payload: TestPlanCreate, project_id: str | None = None, user: CurrentUser = Depends(get_current_user)):
    if project_id and project_id != payload.project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_SCOPE_MISMATCH"})
    await get_project(payload.project_id, user, "testplan.create")
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
    if payload.members:
        await require_action_policy(
            payload.project_id, user, "testplan.assignments", {"QA_LEAD"}
        )
    timestamp = now()
    plan = {"_id": new_id("TP"), **payload.model_dump(), **context, "status": "DRAFT", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    await database.value.test_plans.insert_one(plan)
    await audit(user.id, "test_plan_created", "TestPlan", plan["_id"], payload.project_id)
    return envelope(plan, revision=1)


@router.get("/du-an/{project_id}/ke-hoach-kiem-thu")
async def list_test_plans(
    project_id: str,
    q: str = Query(default="", max_length=300),
    release: str = Query(default="", max_length=200),
    release_id: str = Query(default="", max_length=200),
    build_id: str = Query(default="", max_length=200),
    environment_id: str = Query(default="", max_length=200),
    status: str = Query(default="", max_length=30),
    sort: str = Query(default="-updated_at", max_length=80),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testplan.read")
    query = {"project_id": project_id}
    if q:
        query["$or"] = [
            {"name": {"$regex": re.escape(q), "$options": "i"}},
            {"objective": {"$regex": re.escape(q), "$options": "i"}},
        ]
    for field, value in {
        "release": release,
        "release_id": release_id,
        "build_id": build_id,
        "environment_id": environment_id,
        "status": status,
    }.items():
        if value:
            query[field] = value
    sort_field, direction = sort_spec(
        sort, {"name", "release", "status", "created_at", "updated_at"}
    )
    return envelope(await database.value.test_plans.find(query).sort(sort_field, direction).to_list(500))


@router.get("/ke-hoach-kiem-thu/{plan_id}")
async def get_test_plan(plan_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(await get_project_entity("test_plans", plan_id, user, "testplan.read"))


@router.patch("/ke-hoach-kiem-thu/{plan_id}")
async def update_test_plan(plan_id: str, payload: TestPlanPatch, user: CurrentUser = Depends(get_current_user)):
    plan = await get_project_entity("test_plans", plan_id, user, "testplan.update")
    if plan.get("status") != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "TEST_PLAN_NOT_DRAFT"})
    if payload.members is not None:
        await require_action_policy(
            plan["project_id"], user, "testplan.assignments", {"QA_LEAD"}
        )
    changes = payload.model_dump(exclude_unset=True)
    if {"release_id", "build_id", "environment_id", "release", "build", "environment"} & set(changes):
        changes.update(
            await resolve_execution_context(
                plan["project_id"],
                user,
                release_id=changes.get("release_id", plan.get("release_id")),
                build_id=changes.get("build_id", plan.get("build_id")),
                environment_id=changes.get("environment_id", plan.get("environment_id")),
                release=changes.get("release", plan.get("release", "")),
                build=changes.get("build", plan.get("build", "")),
                environment=changes.get("environment", plan.get("environment", "")),
            )
        )
    updated = await optimistic_patch("test_plans", plan_id, plan["project_id"], payload.expected_revision, changes)
    await audit(user.id, "test_plan_updated", "TestPlan", plan_id, plan["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/ke-hoach-kiem-thu/{plan_id}/gui-ra-soat")
async def submit_test_plan(plan_id: str, payload: ReviewTransitionInput, user: CurrentUser = Depends(get_current_user)):
    plan = await get_project_entity("test_plans", plan_id, user, "testplan.submit_review")
    if plan.get("status") != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    updated = await optimistic_patch("test_plans", plan_id, plan["project_id"], payload.expected_revision, {"status": "IN_REVIEW", "review_note": payload.review_note})
    await audit(user.id, "test_plan_submitted", "TestPlan", plan_id, plan["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/ke-hoach-kiem-thu/{plan_id}/phe-duyet")
async def approve_test_plan(plan_id: str, payload: ReviewTransitionInput, user: CurrentUser = Depends(get_current_user)):
    plan = await get_project_entity("test_plans", plan_id, user, "testplan.approve")
    if plan.get("status") not in {"DRAFT", "IN_REVIEW"}:
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    updated = await optimistic_patch("test_plans", plan_id, plan["project_id"], payload.expected_revision, {"status": "APPROVED", "approved_by": user.id, "approved_at": now(), "review_note": payload.review_note})
    await audit(user.id, "test_plan_approved", "TestPlan", plan_id, plan["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/ke-hoach-kiem-thu/{plan_id}/luu-tru")
async def archive_test_plan(plan_id: str, payload: ProjectArchiveInput, user: CurrentUser = Depends(get_current_user)):
    plan = await get_project_entity("test_plans", plan_id, user, "testplan.archive")
    updated = await optimistic_patch("test_plans", plan_id, plan["project_id"], payload.expected_revision, {"status": "ARCHIVED", "archive_reason": payload.reason, "archived_by": user.id, "archived_at": now()})
    await audit(user.id, "test_plan_archived", "TestPlan", plan_id, plan["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/ke-hoach-kiem-thu/{plan_id}/nhan-ban", status_code=201)
async def clone_test_plan(plan_id: str, user: CurrentUser = Depends(get_current_user)):
    plan = await get_project_entity("test_plans", plan_id, user, "testplan.create")
    timestamp = now()
    cloned = {**plan, "_id": new_id("TP"), "name": f"{plan['name']} bản sao", "status": "DRAFT", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    for field in ["approved_at", "approved_by", "archived_at", "archived_by", "archive_reason", "reviewed_at", "reviewed_by"]:
        cloned.pop(field, None)
    await database.value.test_plans.insert_one(cloned)
    await audit(user.id, "test_plan_cloned", "TestPlan", cloned["_id"], plan["project_id"], {"source_plan_id": plan_id})
    return envelope(cloned, revision=1)


@router.post("/bo-kiem-thu", status_code=201)
@router.post("/du-an/{project_id}/bo-kiem-thu", status_code=201)
async def create_test_suite(payload: TestSuiteCreate, project_id: str | None = None, user: CurrentUser = Depends(get_current_user)):
    if project_id and project_id != payload.project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_SCOPE_MISMATCH"})
    await get_project(payload.project_id, user, "testsuite.create")
    await validate_test_versions(payload.project_id, payload.test_case_version_ids)
    timestamp = now()
    suite = {"_id": new_id("TSU"), **payload.model_dump(), "status": "ACTIVE", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    await database.value.test_suites.insert_one(suite)
    await audit(user.id, "test_suite_created", "TestSuite", suite["_id"], payload.project_id)
    return envelope(suite, revision=1)


@router.get("/du-an/{project_id}/bo-kiem-thu")
async def list_test_suites(
    project_id: str,
    q: str = Query(default="", max_length=300),
    suite_type: str = Query(default="", max_length=40),
    status: str = Query(default="", max_length=30),
    sort: str = Query(default="-updated_at", max_length=80),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testsuite.read")
    query = {"project_id": project_id}
    if q:
        query["name"] = {"$regex": re.escape(q), "$options": "i"}
    for field, value in {"suite_type": suite_type, "status": status}.items():
        if value:
            query[field] = value
    sort_field, direction = sort_spec(
        sort, {"name", "suite_type", "status", "created_at", "updated_at"}
    )
    return envelope(await database.value.test_suites.find(query).sort(sort_field, direction).to_list(500))


@router.get("/bo-kiem-thu/{suite_id}")
async def get_test_suite(suite_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(await get_project_entity("test_suites", suite_id, user, "testsuite.read"))


@router.patch("/bo-kiem-thu/{suite_id}")
async def update_test_suite(suite_id: str, payload: TestSuitePatch, user: CurrentUser = Depends(get_current_user)):
    suite = await get_project_entity("test_suites", suite_id, user, "testsuite.update")
    if suite.get("status", "ACTIVE") == "ARCHIVED":
        raise HTTPException(status_code=409, detail={"code": "TEST_SUITE_ARCHIVED"})
    if payload.test_case_version_ids is not None:
        await validate_test_versions(suite["project_id"], payload.test_case_version_ids)
    updated = await optimistic_patch("test_suites", suite_id, suite["project_id"], payload.expected_revision, payload.model_dump())
    await audit(user.id, "test_suite_updated", "TestSuite", suite_id, suite["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/bo-kiem-thu/{suite_id}/nhan-ban", status_code=201)
async def clone_test_suite(suite_id: str, user: CurrentUser = Depends(get_current_user)):
    suite = await get_project_entity("test_suites", suite_id, user, "testsuite.clone")
    timestamp = now()
    cloned = {**suite, "_id": new_id("TSU"), "name": f"{suite['name']} bản sao", "status": "ACTIVE", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    for field in ["archived_at", "archived_by", "archive_reason"]:
        cloned.pop(field, None)
    await database.value.test_suites.insert_one(cloned)
    await audit(user.id, "test_suite_cloned", "TestSuite", cloned["_id"], suite["project_id"], {"source_suite_id": suite_id})
    return envelope(cloned, revision=1)


@router.post("/bo-kiem-thu/{suite_id}/luu-tru")
async def archive_test_suite(suite_id: str, payload: ProjectArchiveInput, user: CurrentUser = Depends(get_current_user)):
    suite = await get_project_entity("test_suites", suite_id, user, "testsuite.archive")
    updated = await optimistic_patch("test_suites", suite_id, suite["project_id"], payload.expected_revision, {"status": "ARCHIVED", "archive_reason": payload.reason, "archived_by": user.id, "archived_at": now()})
    await audit(user.id, "test_suite_archived", "TestSuite", suite_id, suite["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/lan-chay-kiem-thu", status_code=201)
@router.post("/du-an/{project_id}/lan-chay-kiem-thu", status_code=201)
async def create_test_run(payload: TestRunCreate, project_id: str | None = None, user: CurrentUser = Depends(get_current_user)):
    if project_id is not None and payload.project_id != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    await get_project(payload.project_id, user, "testrun.create")
    plan = None
    if payload.test_plan_id:
        plan = await database.value.test_plans.find_one(
            {"_id": payload.test_plan_id, "project_id": payload.project_id}
        )
        if not plan:
            raise HTTPException(status_code=422, detail={"code": "INVALID_TEST_PLAN"})
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
        suites = await database.value.test_suites.find({"project_id": payload.project_id, "_id": {"$in": payload.test_suite_ids}}).to_list(500)
        if len(suites) != len(set(payload.test_suite_ids)):
            raise HTTPException(status_code=422, detail={"code": "INVALID_TEST_SUITE"})
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
    run = {"_id": new_id("TRUN"), **payload.model_dump(), **context, **device_scope, "test_case_version_ids": version_ids, "status": "DRAFT", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    await database.value.test_runs.insert_one(run)
    if version_ids:
        try:
            await database.value.test_results.insert_many(
                [
                    {
                        "_id": new_id("TRES"),
                        "project_id": payload.project_id,
                        "test_run_id": run["_id"],
                        "test_case_version_id": version_id,
                        "environment": context["environment"],
                        "environment_id": context["environment_id"],
                        "release": context["release"],
                        "release_id": context["release_id"],
                        "build": context["build"],
                        "build_id": context["build_id"],
                        "status": "NOT_RUN",
                        "step_results": [],
                        "actual_result_doc": {"type": "doc", "content": []},
                        "attachments": [],
                        "note": "",
                        "idempotency_key": None,
                        "revision": 1,
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
            await database.value.test_results.delete_many({"test_run_id": run["_id"], "project_id": payload.project_id})
            await database.value.test_runs.delete_one({"_id": run["_id"], "project_id": payload.project_id})
            raise
    await audit(user.id, "test_run_created", "TestRun", run["_id"], payload.project_id, {"test_count": len(version_ids)})
    return envelope(run, revision=1)


@router.patch("/du-an/{project_id}/lan-chay-kiem-thu/{run_id}")
async def update_test_run(
    project_id: str,
    run_id: str,
    payload: TestRunPatch,
    user: CurrentUser = Depends(get_current_user),
):
    run = await get_project_entity("test_runs", run_id, user, "testrun.update")
    if run["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    if run.get("status") != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "TEST_RUN_SCOPE_FROZEN"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    version_ids = changes.get("test_case_version_ids", run.get("test_case_version_ids", []))
    if "test_suite_ids" in changes:
        suites = await database.value.test_suites.find({"project_id": project_id, "_id": {"$in": changes["test_suite_ids"]}}).to_list(500)
        if len(suites) != len(set(changes["test_suite_ids"])):
            raise HTTPException(status_code=422, detail={"code": "INVALID_TEST_SUITE"})
        version_ids = list(dict.fromkeys([*version_ids, *[item for suite in suites for item in suite.get("test_case_version_ids", [])]]))
        changes["test_case_version_ids"] = version_ids
    if "test_case_version_ids" in changes:
        await validate_test_versions(project_id, version_ids)
    if {"release_id", "build_id", "environment_id", "release", "build", "environment"} & set(changes):
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
    updated = await optimistic_patch("test_runs", run_id, project_id, payload.expected_revision, changes)
    await audit(user.id, "test_run_updated", "TestRun", run_id, project_id)
    return envelope(updated, revision=updated["revision"])


@router.post("/du-an/{project_id}/lan-chay-kiem-thu/{run_id}/phan-cong")
async def assign_test_run(
    project_id: str,
    run_id: str,
    payload: TestRunAssignmentInput,
    user: CurrentUser = Depends(get_current_user),
):
    run = await get_project_entity("test_runs", run_id, user, "testrun.assign")
    if run["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    if payload.assignee_id:
        assignee = await database.value.project_members.find_one(
            {
                "project_id": project_id,
                "user_id": payload.assignee_id,
                "status": "ACTIVE",
                "project_role": "TESTER",
            }
        )
        if not assignee:
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_TEST_RUN_ASSIGNEE", "user_id": payload.assignee_id},
            )
    assigned_users = set(payload.test_case_assignments.values())
    if assigned_users:
        valid_members = await database.value.project_members.count_documents(
            {
                "project_id": project_id,
                "user_id": {"$in": list(assigned_users)},
                "status": "ACTIVE",
                "project_role": "TESTER",
            }
        )
        if valid_members != len(assigned_users):
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_TEST_CASE_ASSIGNEE"},
            )
    unknown = set(payload.test_case_assignments) - set(run.get("test_case_version_ids", []))
    if unknown:
        raise HTTPException(status_code=422, detail={"code": "TEST_NOT_IN_RUN_SNAPSHOT", "test_case_version_ids": sorted(unknown)})
    updated = await optimistic_patch("test_runs", run_id, project_id, payload.expected_revision, {"assignee_id": payload.assignee_id, "test_case_assignments": payload.test_case_assignments})
    await audit(user.id, "test_run_assigned", "TestRun", run_id, project_id, {"assignee_id": payload.assignee_id})
    return envelope(updated, revision=updated["revision"])


@router.get("/du-an/{project_id}/lan-chay-kiem-thu")
async def list_test_runs(
    project_id: str,
    name: str = Query(default="", max_length=300),
    release: str = Query(default="", max_length=200),
    release_id: str = Query(default="", max_length=200),
    build: str = Query(default="", max_length=200),
    build_id: str = Query(default="", max_length=200),
    environment: str = Query(default="", max_length=200),
    environment_id: str = Query(default="", max_length=200),
    status: str = Query(default="", max_length=30),
    created_by: str = Query(default="", max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    sort: str = Query(default="-updated_at", max_length=80),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testrun.read")
    query = {"project_id": project_id}
    if name:
        query["name"] = {"$regex": re.escape(name), "$options": "i"}
    if status:
        query["status"] = status
    for field, value in {
        "release": release,
        "release_id": release_id,
        "build": build,
        "build_id": build_id,
        "environment": environment,
        "environment_id": environment_id,
        "created_by": created_by,
    }.items():
        if value:
            query[field] = value
    sort_field, direction = sort_spec(
        sort,
        {"name", "release", "build", "environment", "status", "created_by", "created_at", "updated_at"},
    )
    total = await database.value.test_runs.count_documents(query)
    items = await database.value.test_runs.find(query).sort(sort_field, direction).skip(
        (page - 1) * page_size
    ).limit(page_size).to_list(page_size)
    return envelope(page_payload(items, page, page_size, total))


@router.get("/du-an/{project_id}/ket-qua-kiem-thu")
async def list_test_results(
    project_id: str,
    status: str = Query(default="", max_length=100),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testrun.read")
    query = {"project_id": project_id}
    statuses = [value.strip() for value in status.split(",") if value.strip()]
    if statuses:
        allowed = {"NOT_RUN", "IN_PROGRESS", "PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"}
        if not set(statuses) <= allowed:
            raise HTTPException(status_code=422, detail={"code": "INVALID_TEST_RESULT_STATUS"})
        query["status"] = {"$in": statuses}
    return envelope(await database.value.test_results.find(query).sort("updated_at", -1).to_list(5000))


@router.get("/lan-chay-kiem-thu/{run_id}")
async def get_test_run(run_id: str, user: CurrentUser = Depends(get_current_user)):
    run = await get_project_entity("test_runs", run_id, user, "testrun.read")
    versions = await database.value.test_case_versions.find({"_id": {"$in": run["test_case_version_ids"]}}).to_list(10000)
    results = await database.value.test_results.find({"test_run_id": run_id}).to_list(10000)
    defects = await database.value.defects.find({"project_id": run["project_id"], "linked_test_result_id": {"$in": [item["_id"] for item in results]}}).to_list(10000)
    return envelope({**run, "test_case_versions": versions, "results": results, "defects": defects})


@router.get("/lan-chay-kiem-thu/{run_id}/bao-cao")
async def export_test_run_report(run_id: str, user: CurrentUser = Depends(get_current_user)):
    run = await get_project_entity("test_runs", run_id, user, "report.export")
    versions = await database.value.test_case_versions.find({"_id": {"$in": run["test_case_version_ids"]}}).to_list(10000)
    results = await database.value.test_results.find({"test_run_id": run_id}).to_list(10000)
    by_result = {item["test_case_version_id"]: item for item in results}
    fields = ["run_id", "run_name", "environment", "build", "test_case_key", "test_case_version", "title", "result", "executed_by", "executed_at", "note"]
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for version in versions:
        result = by_result.get(version["_id"], {})
        writer.writerow({"run_id": run_id, "run_name": run["name"], "environment": run.get("environment"), "build": run.get("build"), "test_case_key": version.get("test_case_key"), "test_case_version": version.get("version"), "title": version.get("title"), "result": result.get("status", "NOT_RUN"), "executed_by": result.get("executed_by"), "executed_at": result.get("executed_at"), "note": result.get("note")})
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="test-run-{run_id}.csv"'})


@router.post("/lan-chay-kiem-thu/{run_id}/bat-dau")
async def start_test_run(run_id: str, user: CurrentUser = Depends(get_current_user)):
    run = await get_project_entity("test_runs", run_id, user, "testrun.start")
    if run["status"] == "IN_PROGRESS":
        return envelope(run)
    if run["status"] not in {"DRAFT", "READY"}:
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    scope = frozen_run_scope(run)
    scope_fingerprint = frozen_run_scope_hash(scope)
    updated = await database.value.test_runs.find_one_and_update(
        {"_id": run_id, "status": run["status"], "revision": run.get("revision", 1)},
        {
            "$set": {
                "status": "IN_PROGRESS",
                "frozen_scope": scope,
                "frozen_scope_hash": scope_fingerprint,
                "started_at": now(),
                "started_by": user.id,
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "test_run_started", "TestRun", run_id, run["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post(
    "/du-an/{project_id}/lan-chay-kiem-thu/{run_id}/tiep-tuc",
    openapi_extra={"x-function-ids": ["RUN-15"]},
)
async def resume_test_run(
    project_id: str,
    run_id: str,
    payload: TestRunResumeInput,
    user: CurrentUser = Depends(get_current_user),
):
    run = await get_project_entity("test_runs", run_id, user, "testrun.execute")
    if run["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    existing = await database.value.test_run_resume_events.find_one(
        {"test_run_id": run_id, "idempotency_key": payload.idempotency_key}
    )
    if existing:
        return envelope(await replay_resume_event(run, existing), revision=run.get("revision", 1))
    if run.get("status") != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail={"code": "TEST_RUN_NOT_IN_PROGRESS"})
    if run.get("revision", 1) != payload.expected_revision:
        raise HTTPException(
            status_code=409,
            detail={"code": "REVISION_CONFLICT", "current_revision": run.get("revision", 1)},
        )
    scope = frozen_run_scope(run)
    scope_fingerprint = frozen_run_scope_hash(scope)
    if run.get("frozen_scope_hash") and run["frozen_scope_hash"] != scope_fingerprint:
        raise HTTPException(status_code=409, detail={"code": "TEST_RUN_SCOPE_CHANGED"})
    selected = await select_resume_execution(run, user)
    timestamp = now()
    event = {
        "_id": new_id("RSM"),
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
        await database.value.test_run_resume_events.insert_one(event)
    except DuplicateKeyError:
        existing = await database.value.test_run_resume_events.find_one(
            {"test_run_id": run_id, "idempotency_key": payload.idempotency_key}
        )
        return envelope(await replay_resume_event(run, existing), revision=run.get("revision", 1))
    updated = await database.value.test_runs.find_one_and_update(
        {
            "_id": run_id,
            "project_id": project_id,
            "status": "IN_PROGRESS",
            "revision": payload.expected_revision,
        },
        {
            "$set": {
                "frozen_scope": run.get("frozen_scope") or scope,
                "frozen_scope_hash": scope_fingerprint,
                "last_resumed_at": timestamp,
                "last_resumed_by": user.id,
                "last_resume_event_id": event["_id"],
                "updated_at": timestamp,
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        await database.value.test_run_resume_events.delete_one({"_id": event["_id"]})
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await database.value.test_run_resume_events.update_one(
        {"_id": event["_id"]}, {"$set": {"run_revision": updated["revision"]}}
    )
    event["run_revision"] = updated["revision"]
    await audit(
        user.id,
        "test_run_resumed",
        "TestRun",
        run_id,
        project_id,
        {
            "resume_event_id": event["_id"],
            "current_test_case_version_id": event["current_test_case_version_id"],
            "scope_fingerprint": scope_fingerprint,
        },
    )
    return envelope(
        {
            "run": updated,
            "resume_event": event,
            **selected,
            "scope_fingerprint": scope_fingerprint,
        },
        revision=updated["revision"],
    )


@router.post("/lan-chay-kiem-thu/{run_id}/ket-qua/{test_case_version_id}")
async def record_test_result(
    run_id: str,
    test_case_version_id: str,
    payload: TestResultInput,
    user: CurrentUser = Depends(get_current_user),
):
    run = await get_project_entity("test_runs", run_id, user, "testrun.execute")
    if run["status"] != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail={"code": "TEST_RUN_NOT_IN_PROGRESS"})
    if test_case_version_id not in run["test_case_version_ids"]:
        raise HTTPException(status_code=422, detail={"code": "TEST_NOT_IN_RUN_SNAPSHOT"})
    existing = await database.value.test_results.find_one({"test_run_id": run_id, "test_case_version_id": test_case_version_id})
    if existing:
        if existing.get("idempotency_key") == payload.idempotency_key:
            return envelope(existing)
    await enforce_not_applicable_policy(run["project_id"], payload.status, payload.step_results)
    if existing:
        if existing.get("status") != "NOT_RUN":
            raise HTTPException(status_code=409, detail={"code": "RESULT_ALREADY_RECORDED"})
        timestamp = now()
        result = await database.value.test_results.find_one_and_update(
            {"_id": existing["_id"], "project_id": run["project_id"], "status": "NOT_RUN", "revision": existing.get("revision", 1)},
            {
                "$set": {
                    **payload.model_dump(),
                    "executor_id": user.id,
                    "executed_by": user.id,
                    "started_at": existing.get("started_at") or timestamp,
                    "completed_at": timestamp,
                    "executed_at": timestamp,
                    "updated_at": timestamp,
                },
                "$inc": {"revision": 1},
            },
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            raise HTTPException(status_code=409, detail={"code": "EXECUTION_CONFLICT"})
    else:
        result = {"_id": new_id("TRES"), "project_id": run["project_id"], "test_run_id": run_id, "test_case_version_id": test_case_version_id, "environment": run.get("environment"), "build": run.get("build"), **payload.model_dump(), "revision": 1, "executor_id": user.id, "executed_by": user.id, "started_at": now(), "completed_at": now(), "executed_at": now(), "created_at": now(), "updated_at": now()}
        await database.value.test_results.insert_one(result)
    await database.value.test_runs.update_one({"_id": run_id}, {"$set": {"updated_at": now()}, "$inc": {"revision": 1}})
    await audit(user.id, "test_result_recorded", "TestResult", result["_id"], run["project_id"], {"status": payload.status})
    return envelope(result)


@router.patch("/du-an/{project_id}/thuc-thi-kiem-thu/{execution_id}")
async def patch_test_execution(
    project_id: str,
    execution_id: str,
    payload: TestExecutionPatch,
    user: CurrentUser = Depends(get_current_user),
):
    result = await get_project_entity("test_results", execution_id, user, "testrun.execute")
    if result["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    existing_event = await database.value.test_execution_updates.find_one(
        {"test_result_id": execution_id, "idempotency_key": payload.idempotency_key}
    )
    if existing_event:
        return envelope({"execution": await database.value.test_results.find_one({"_id": execution_id}), "update": existing_event})
    await enforce_not_applicable_policy(project_id, payload.status, payload.step_results)
    run = await database.value.test_runs.find_one({"_id": result["test_run_id"], "project_id": project_id})
    if not run or run.get("status") != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail={"code": "TEST_RUN_NOT_IN_PROGRESS"})
    allowed = EXECUTION_TRANSITIONS.get(result.get("status"), set())
    if payload.status not in allowed:
        raise HTTPException(status_code=409, detail={"code": "INVALID_EXECUTION_TRANSITION", "from": result.get("status"), "to": payload.status})
    expected_revision = payload.expected_revision or result.get("revision", 1)
    timestamp = now()
    terminal = payload.status in {"PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"}
    updated = await database.value.test_results.find_one_and_update(
        {"_id": execution_id, "project_id": project_id, "revision": expected_revision},
        {
            "$set": {
                "status": payload.status,
                "step_results": [item.model_dump() for item in payload.step_results],
                "actual_result_doc": payload.actual_result_doc,
                "attachments": payload.attachments,
                "note": payload.note,
                "executor_id": user.id,
                "executed_by": user.id,
                "started_at": result.get("started_at") or timestamp,
                "completed_at": timestamp if terminal else None,
                "updated_at": timestamp,
                "last_updated_by": user.id,
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    event = {
        "_id": new_id("TEU"),
        "project_id": project_id,
        "test_result_id": execution_id,
        "from_status": result.get("status"),
        "to_status": payload.status,
        "idempotency_key": payload.idempotency_key,
        "updated_by": user.id,
        "created_at": now(),
    }
    try:
        await database.value.test_execution_updates.insert_one(event)
    except DuplicateKeyError:
        event = await database.value.test_execution_updates.find_one(
            {"test_result_id": execution_id, "idempotency_key": payload.idempotency_key}
        )
    await database.value.test_runs.update_one(
        {"_id": result["test_run_id"], "project_id": project_id},
        {"$set": {"updated_at": now()}, "$inc": {"revision": 1}},
    )
    await audit(user.id, "test_execution_updated", "TestExecution", execution_id, project_id, {"status": payload.status})
    return envelope({"execution": updated, "update": event}, revision=updated["revision"])


@router.post("/ket-qua-kiem-thu/{result_id}/hieu-chinh")
async def correct_test_result(result_id: str, payload: TestResultCorrectionInput, user: CurrentUser = Depends(get_current_user)):
    result = await get_project_entity(
        "test_results", result_id, user, "testresult.correct"
    )
    existing = await database.value.test_result_corrections.find_one({"test_result_id": result_id, "idempotency_key": payload.idempotency_key})
    if existing:
        return envelope({"result": await database.value.test_results.find_one({"_id": result_id}), "correction": existing})
    await enforce_not_applicable_policy(result["project_id"], payload.status)
    event = {"_id": new_id("TRC"), "project_id": result["project_id"], "test_result_id": result_id, "from_status": result.get("status"), "to_status": payload.status, "reason": payload.reason, "idempotency_key": payload.idempotency_key, "corrected_by": user.id, "created_at": now()}
    try:
        await database.value.test_result_corrections.insert_one(event)
    except DuplicateKeyError:
        event = await database.value.test_result_corrections.find_one({"test_result_id": result_id, "idempotency_key": payload.idempotency_key})
        return envelope({"result": await database.value.test_results.find_one({"_id": result_id}), "correction": event})
    await database.value.test_results.update_one({"_id": result_id}, {"$set": {"status": payload.status, "corrected": True, "last_correction_id": event["_id"], "completed_at": now(), "updated_at": now()}, "$push": {"correction_event_ids": event["_id"]}, "$inc": {"revision": 1}})
    await audit(user.id, "test_result_corrected", "TestResult", result_id, result["project_id"], {"from": result.get("status"), "to": payload.status, "correction_id": event["_id"]})
    return envelope({"result": await database.value.test_results.find_one({"_id": result_id}), "correction": event})


@router.post("/lan-chay-kiem-thu/{run_id}/hoan-tat")
async def complete_test_run(run_id: str, user: CurrentUser = Depends(get_current_user)):
    run = await get_project_entity("test_runs", run_id, user, "testrun.complete")
    if run["status"] == "COMPLETED":
        return envelope(run)
    if run["status"] != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    result_count = await database.value.test_results.count_documents({"test_run_id": run_id, "status": {"$in": ["PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"]}})
    total_count = len(run["test_case_version_ids"])
    project = await database.value.projects.find_one(
        {"_id": run["project_id"]}, {"settings": 1}
    )
    partial_allowed = bool(
        (project.get("settings") or {}).get("partial_complete_allowed", False)
    )
    if result_count < total_count and not partial_allowed:
        raise HTTPException(status_code=409, detail={"code": "PARTIAL_EXECUTION", "completed": result_count, "total": len(run["test_case_version_ids"])})
    partial_completion = result_count < total_count
    await database.value.test_runs.update_one({"_id": run_id}, {"$set": {"status": "COMPLETED", "completed_at": now(), "completed_by": user.id, "completed_result_count": result_count, "total_result_count": total_count, "partial_completion": partial_completion, "updated_at": now()}, "$inc": {"revision": 1}})
    await audit(user.id, "test_run_completed", "TestRun", run_id, run["project_id"], {"completed": result_count, "total": total_count, "partial_completion": partial_completion})
    return envelope(await database.value.test_runs.find_one({"_id": run_id}))


@router.post("/lan-chay-kiem-thu/{run_id}/huy")
async def abort_test_run(run_id: str, reason: str = Body(embed=True, min_length=2, max_length=2000), user: CurrentUser = Depends(get_current_user)):
    run = await get_project_entity("test_runs", run_id, user, "testrun.abort")
    if run["status"] not in {"DRAFT", "READY", "IN_PROGRESS"}:
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    await database.value.test_runs.update_one({"_id": run_id}, {"$set": {"status": "ABORTED", "abort_reason": reason, "aborted_by": user.id, "aborted_at": now(), "updated_at": now()}, "$inc": {"revision": 1}})
    await audit(user.id, "test_run_aborted", "TestRun", run_id, run["project_id"], {"reason": reason})
    return envelope(await database.value.test_runs.find_one({"_id": run_id}))


@router.post("/du-an/{project_id}/loi", status_code=201)
async def create_defect(project_id: str, payload: DefectCreate, user: CurrentUser = Depends(get_current_user)):
    if project_id != payload.project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    await get_project(project_id, user, "defect.create")
    context = await resolve_execution_context(
        project_id,
        user,
        release_id=payload.release_id,
        build_id=payload.build_id,
        environment_id=payload.environment_id,
        release=payload.release,
        build=payload.build,
        environment=payload.environment,
    )
    if payload.linked_test_result_id:
        result = await database.value.test_results.find_one({"_id": payload.linked_test_result_id, "project_id": project_id})
        if not result or result["status"] != "FAIL":
            raise HTTPException(status_code=422, detail={"code": "DEFECT_REQUIRES_FAILED_RESULT"})
    timestamp = now()
    defect = {"_id": new_id("DEF"), **payload.model_dump(), **context, "defect_key": payload.defect_key or await next_key(project_id, "defect", "DEF"), "status": "NEW", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    await database.value.defects.insert_one(defect)
    await index_artifact(project_id, "defect", defect["_id"], defect["_id"], defect["title"], " ".join([defect["title"], str(defect.get("environment", "")), str(defect.get("build", ""))]), defect["status"], "record", 1)
    await audit(user.id, "defect_created", "Defect", defect["_id"], project_id)
    return envelope(defect, revision=1)


@router.get("/du-an/{project_id}/loi")
async def list_defects(
    project_id: str,
    q: str = Query(default="", max_length=300),
    key: str = Query(default="", max_length=80),
    title: str = Query(default="", max_length=300),
    status: str = Query(default="", max_length=40),
    severity: str = Query(default="", max_length=30),
    priority: str = Query(default="", max_length=30),
    assignee: str = Query(default="", max_length=200),
    release: str = Query(default="", max_length=200),
    release_id: str = Query(default="", max_length=200),
    environment: str = Query(default="", max_length=500),
    environment_id: str = Query(default="", max_length=200),
    build: str = Query(default="", max_length=200),
    build_id: str = Query(default="", max_length=200),
    requirement_id: str = Query(default="", max_length=200),
    test_case_id: str = Query(default="", max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    sort: str = Query(default="-updated_at", max_length=80),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "defect.read")
    query = {"project_id": project_id}
    search_terms = [value.strip() for value in (q, key, title) if value.strip()]
    if search_terms:
        query["$and"] = [
            {
                "$or": [
                    {"defect_key": {"$regex": re.escape(value), "$options": "i"}},
                    {"title": {"$regex": re.escape(value), "$options": "i"}},
                ]
            }
            for value in search_terms
        ]
    if status:
        query["status"] = status
    for field, value in {
        "severity": severity,
        "priority": priority,
        "assignee": assignee,
        "release": release,
        "release_id": release_id,
        "environment": environment,
        "environment_id": environment_id,
        "build": build,
        "build_id": build_id,
        "linked_test_case_version_id": test_case_id,
    }.items():
        if value:
            query[field] = value
    if requirement_id:
        version_ids = [
            item["_id"]
            for item in await database.value.requirement_versions.find(
                {"project_id": project_id, "requirement_id": requirement_id}, {"_id": 1}
            ).to_list(1000)
        ]
        version_ids.append(requirement_id)
        query["linked_requirement_version_ids"] = {"$in": version_ids}
    if test_case_id:
        version_ids = [
            item["_id"]
            for item in await database.value.test_case_versions.find(
                {"project_id": project_id, "test_case_id": test_case_id}, {"_id": 1}
            ).to_list(1000)
        ]
        version_ids.append(test_case_id)
        query["linked_test_case_version_id"] = {"$in": version_ids}
    sort_field, direction = sort_spec(
        sort,
        {"defect_key", "title", "status", "severity", "priority", "assignee", "release", "build", "environment", "created_at", "updated_at"},
    )
    total = await database.value.defects.count_documents(query)
    items = await database.value.defects.find(query).sort(sort_field, direction).skip(
        (page - 1) * page_size
    ).limit(page_size).to_list(page_size)
    return envelope(page_payload(items, page, page_size, total))


@router.get("/du-an/{project_id}/loi/trung-lap")
async def find_duplicate_defects(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "defect.duplicate_check")
    defects = await database.value.defects.find(
        {"project_id": project_id, "status": {"$nin": ["REJECTED", "DUPLICATE"]}}
    ).sort("updated_at", -1).to_list(2000)
    pairs = []
    for index, left in enumerate(defects):
        left_text = " ".join(
            [left.get("title", ""), plain_text(left.get("description_doc", {}))]
        ).lower()
        for right in defects[index + 1 :]:
            right_text = " ".join(
                [right.get("title", ""), plain_text(right.get("description_doc", {}))]
            ).lower()
            similarity = round(SequenceMatcher(None, left_text, right_text).ratio(), 4)
            if similarity >= 0.65:
                pairs.append(
                    {
                        "_id": f"{left['_id']}:{right['_id']}",
                        "left": left,
                        "right": right,
                        "similarity": similarity,
                        "reason": "Tiêu đề và mô tả có mức tương đồng cao",
                    }
                )
    pairs.sort(key=lambda item: item["similarity"], reverse=True)
    return envelope(pairs[:100])


@router.get("/du-an/{project_id}/loi/xuat")
async def export_defects(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "report.export")
    defects = await database.value.defects.find({"project_id": project_id}).to_list(10000)
    fields = ["defect_key", "title", "severity", "priority", "status", "environment", "build", "assignee"]
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for defect in defects:
        writer.writerow({field: defect.get(field) for field in fields})
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="defects-{project_id}.csv"'})


@router.get(
    "/du-an/{project_id}/loi/{defect_id}",
    openapi_extra={"x-function-ids": ["DEF-02"]},
)
@router.get("/loi/{defect_id}", openapi_extra={"x-function-ids": ["DEF-02"]})
async def defect_detail(
    defect_id: str,
    project_id: str | None = None,
    user: CurrentUser = Depends(get_current_user),
):
    defect = await get_project_entity("defects", defect_id, user, "defect.read")
    if project_id is not None and defect["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    trace_links = await database.value.trace_links.find(
        {
            "project_id": defect["project_id"],
            "$or": [
                {"source_type": "defect", "source_id": defect_id},
                {"target_type": "defect", "target_id": defect_id},
            ],
        }
    ).sort("created_at", -1).to_list(500)
    comments = await database.value.review_comments.find(
        {
            "project_id": defect["project_id"],
            "artifact_type": "defect",
            "artifact_id": defect_id,
        }
    ).sort("created_at", 1).to_list(500)
    attachments = await database.value.attachments.find(
        {
            "project_id": defect["project_id"],
            "artifact_type": "defect",
            "artifact_id": defect_id,
            "status": "ACTIVE",
        }
    ).sort("created_at", -1).to_list(500)
    return envelope(
        {
            **defect,
            "trace_links": trace_links,
            "comments": comments,
            "attachments": attachments,
        },
        revision=defect.get("revision", 1),
    )


async def build_defect_trace_candidates(defect):
    text = " ".join(
        [
            defect.get("title", ""),
            plain_text(defect.get("description_doc", {})),
            plain_text(defect.get("actual_result_doc", {})),
            plain_text(defect.get("expected_result_doc", {})),
        ]
    ).lower()
    requirements = await database.value.requirements.find(
        {"project_id": defect["project_id"], "status": {"$ne": "OBSOLETE"}}
    ).to_list(2000)
    requirement_version_ids = [
        item.get("current_version_id") for item in requirements if item.get("current_version_id")
    ]
    requirement_versions = await database.value.requirement_versions.find(
        {"project_id": defect["project_id"], "_id": {"$in": requirement_version_ids}}
    ).to_list(2000)
    requirement_by_version = {
        item.get("current_version_id"): item for item in requirements if item.get("current_version_id")
    }
    test_cases = await database.value.test_cases.find(
        {"project_id": defect["project_id"], "status": {"$ne": "OBSOLETE"}}
    ).to_list(2000)
    current_ids = [item.get("current_version_id") for item in test_cases if item.get("current_version_id")]
    versions = await database.value.test_case_versions.find(
        {"project_id": defect["project_id"], "_id": {"$in": current_ids}}
    ).to_list(2000)
    linked_requirements = set(defect.get("linked_requirement_version_ids", []))
    linked_test_version = next(
        (
            item
            for item in versions
            if item["_id"] == defect.get("linked_test_case_version_id")
        ),
        None,
    )
    linked_test_requirements = set(
        linked_test_version.get("requirement_version_ids", []) if linked_test_version else []
    )
    requirement_candidates = []
    for version in requirement_versions:
        requirement = requirement_by_version.get(version["_id"], {})
        version_text = " ".join(
            [
                requirement.get("title", ""),
                version.get("title", ""),
                version.get("plain_text_projection", ""),
                plain_text(version.get("content_doc", {})),
            ]
        ).lower()
        similarity = SequenceMatcher(None, text, version_text).ratio()
        direct = version["_id"] in linked_requirements
        test_trace = version["_id"] in linked_test_requirements
        score = min(1, similarity * 0.7 + (0.35 if direct else 0) + (0.2 if test_trace else 0))
        if score < 0.25:
            continue
        reasons = []
        if direct:
            reasons.append("CURRENT_REQUIREMENT_LINK")
        if test_trace:
            reasons.append("LINKED_TEST_CASE_TRACE")
        if similarity >= 0.3:
            reasons.append("SIMILAR_REQUIREMENT_TEXT")
        requirement_candidates.append(
            {
                "candidate_id": f"requirement_version:{version['_id']}",
                "artifact_type": "requirement_version",
                "artifact_id": version["_id"],
                "requirement_id": version["requirement_id"],
                "requirement_key": version.get("requirement_key")
                or requirement.get("requirement_key"),
                "title": version.get("title") or requirement.get("title", ""),
                "confidence": round(score, 4),
                "confidence_band": "HIGH" if score >= 0.75 else "MEDIUM" if score >= 0.5 else "LOW",
                "reason_codes": reasons,
                "evidence": [
                    {"artifact_type": "defect", "artifact_id": defect["_id"]},
                    {"artifact_type": "requirement_version", "artifact_id": version["_id"]},
                ],
                "proposed_change": {
                    "operation": "ADD_REQUIREMENT_LINK",
                    "linked_requirement_version_id": version["_id"],
                },
            }
        )
    test_case_candidates = []
    for version in versions:
        version_text = " ".join(
            [version.get("title", ""), version.get("plain_text_projection", "")]
        ).lower()
        similarity = SequenceMatcher(None, text, version_text).ratio()
        shared_requirements = linked_requirements & set(version.get("requirement_version_ids", []))
        direct = defect.get("linked_test_case_version_id") == version["_id"]
        score = min(1, similarity * 0.7 + (0.25 if shared_requirements else 0) + (0.3 if direct else 0))
        if score < 0.3:
            continue
        reasons = []
        if direct:
            reasons.append("CURRENT_LINK")
        if shared_requirements:
            reasons.append("SHARED_REQUIREMENT_TRACE")
        if similarity >= 0.35:
            reasons.append("SIMILAR_BEHAVIOR_TEXT")
        test_case_candidates.append(
            {
                "candidate_id": f"test_case_version:{version['_id']}",
                "artifact_type": "test_case_version",
                "artifact_id": version["_id"],
                "test_case_id": version["test_case_id"],
                "test_case_version_id": version["_id"],
                "test_case_key": version["test_case_key"],
                "title": version["title"],
                "requirement_version_ids": version.get("requirement_version_ids", []),
                "confidence": round(score, 4),
                "confidence_band": "HIGH" if score >= 0.75 else "MEDIUM" if score >= 0.5 else "LOW",
                "reason_codes": reasons,
                "evidence": [
                    {"artifact_type": "defect", "artifact_id": defect["_id"]},
                    {"artifact_type": "test_case_version", "artifact_id": version["_id"]},
                ],
                "proposed_change": {
                    "operation": "SET_TEST_CASE_LINK",
                    "linked_test_case_version_id": version["_id"],
                },
            }
        )
    requirement_candidates.sort(key=lambda item: item["confidence"], reverse=True)
    test_case_candidates.sort(key=lambda item: item["confidence"], reverse=True)
    return requirement_candidates[:50], test_case_candidates[:50]


@router.post(
    "/du-an/{project_id}/ai/loi/{defect_id}/goi-y-truy-vet",
    status_code=201,
)
async def suggest_defect_trace(
    project_id: str,
    defect_id: str,
    payload: BugTraceSuggestionInput,
    user: CurrentUser = Depends(get_current_user),
):
    defect = await get_project_entity("defects", defect_id, user, "ai.suggest_bug_trace")
    if defect["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    existing = await database.value.ai_results.find_one(
        {"project_id": project_id, "idempotency_key": payload.idempotency_key}
    )
    if existing:
        if existing.get("subject_id") != defect_id or existing.get("result_type") != "BUG_TRACE_SUGGESTION":
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
        return envelope(existing)
    requirement_candidates, test_case_candidates = await build_defect_trace_candidates(defect)
    result = {
        "_id": new_id("AIR"),
        "project_id": project_id,
        "result_type": "BUG_TRACE_SUGGESTION",
        "subject_type": "defect",
        "subject_id": defect_id,
        "status": "SUCCESS",
        "candidate_only": True,
        "human_confirmation_required": True,
        "requirement_candidates": requirement_candidates,
        "test_case_candidates": test_case_candidates,
        "model": {
            "provider": "hybrid-deterministic",
            "model": "bug-trace-evidence-v1",
            "prompt_version": "bug-trace-v1",
            "tool_schema_version": "1",
            "retrieval_version": "project-filter-v1",
        },
        "idempotency_key": payload.idempotency_key,
        "review_status": "PENDING",
        "revision": 1,
        "created_by": user.id,
        "created_at": now(),
        "updated_at": now(),
    }
    try:
        await database.value.ai_results.insert_one(result)
    except DuplicateKeyError:
        existing = await database.value.ai_results.find_one(
            {"project_id": project_id, "idempotency_key": payload.idempotency_key}
        )
        if not existing:
            raise
        if existing.get("subject_id") != defect_id or existing.get("result_type") != "BUG_TRACE_SUGGESTION":
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
        return envelope(existing)
    await audit(
        user.id,
        "bug_trace_suggestion_generated",
        "AIResult",
        result["_id"],
        project_id,
        {
            "defect_id": defect_id,
            "requirement_candidate_count": len(requirement_candidates),
            "test_case_candidate_count": len(test_case_candidates),
        },
    )
    return envelope(result)


@router.get("/loi/{defect_id}/ung-vien-truy-vet", deprecated=True)
async def find_defect_trace_candidates(
    defect_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    defect = await get_project_entity("defects", defect_id, user, "ai.suggest_bug_trace")
    _, test_case_candidates = await build_defect_trace_candidates(defect)
    return envelope(test_case_candidates)


@router.patch("/du-an/{project_id}/loi/{defect_id}/truy-vet")
async def update_defect_trace(
    project_id: str,
    defect_id: str,
    payload: DefectTraceUpdateInput,
    user: CurrentUser = Depends(get_current_user),
):
    defect = await get_project_entity(
        "defects",
        defect_id,
        user,
        "defect.trace.manage",
        assigned_role="DEVELOPER",
        assigned_user_field="assignee",
    )
    if defect["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    changes = {}
    fields = payload.model_fields_set
    if "linked_test_result_id" in fields:
        if payload.linked_test_result_id:
            result = await database.value.test_results.find_one(
                {
                    "_id": payload.linked_test_result_id,
                    "project_id": project_id,
                    "status": "FAIL",
                }
            )
            if not result:
                raise HTTPException(status_code=422, detail={"code": "DEFECT_REQUIRES_FAILED_RESULT"})
        changes["linked_test_result_id"] = payload.linked_test_result_id
    if "linked_test_case_version_id" in fields:
        if payload.linked_test_case_version_id:
            version = await database.value.test_case_versions.find_one(
                {"_id": payload.linked_test_case_version_id, "project_id": project_id}
            )
            if not version:
                raise HTTPException(status_code=422, detail={"code": "INVALID_TEST_CASE_VERSION"})
        changes["linked_test_case_version_id"] = payload.linked_test_case_version_id
    if "linked_requirement_version_ids" in fields:
        requirement_ids = list(dict.fromkeys(payload.linked_requirement_version_ids or []))
        count = await database.value.requirement_versions.count_documents(
            {"project_id": project_id, "_id": {"$in": requirement_ids}}
        )
        if count != len(requirement_ids):
            raise HTTPException(status_code=422, detail={"code": "INVALID_REQUIREMENT_VERSION"})
        changes["linked_requirement_version_ids"] = requirement_ids
    ai_result = None
    if payload.ai_result_id:
        ai_result = await database.value.ai_results.find_one(
            {
                "_id": payload.ai_result_id,
                "project_id": project_id,
                "result_type": "BUG_TRACE_SUGGESTION",
                "subject_id": defect_id,
            }
        )
        if not ai_result:
            raise HTTPException(status_code=422, detail={"code": "INVALID_AI_RESULT"})
        candidates = ai_result.get("requirement_candidates", []) + ai_result.get(
            "test_case_candidates", []
        )
        candidate_ids = {item.get("candidate_id") for item in candidates}
        if not payload.accepted_candidate_ids or not set(payload.accepted_candidate_ids) <= candidate_ids:
            raise HTTPException(status_code=422, detail={"code": "INVALID_AI_CANDIDATE"})
        accepted = {
            item["candidate_id"]: item
            for item in candidates
            if item.get("candidate_id") in payload.accepted_candidate_ids
        }
        accepted_requirements = {
            item["artifact_id"]
            for item in accepted.values()
            if item.get("artifact_type") == "requirement_version"
        }
        accepted_test_cases = {
            item["artifact_id"]
            for item in accepted.values()
            if item.get("artifact_type") == "test_case_version"
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
            raise HTTPException(status_code=422, detail={"code": "AI_CANDIDATE_CHANGE_MISMATCH"})
    updated = await optimistic_patch(
        "defects", defect_id, project_id, payload.expected_revision, changes
    )
    if ai_result:
        await database.value.ai_results.update_one(
            {"_id": ai_result["_id"], "project_id": project_id},
            {
                "$set": {
                    "review_status": "REVIEWED",
                    "accepted_candidate_ids": list(dict.fromkeys(payload.accepted_candidate_ids)),
                    "review_reason": payload.reason,
                    "reviewed_by": user.id,
                    "reviewed_at": now(),
                    "updated_at": now(),
                },
                "$inc": {"revision": 1},
            },
        )
    await audit(
        user.id,
        "defect_trace_updated",
        "Defect",
        defect_id,
        project_id,
        {
            "reason": payload.reason,
            "changed_fields": sorted(changes),
            "ai_result_id": payload.ai_result_id,
            "accepted_candidate_ids": payload.accepted_candidate_ids,
        },
    )
    return envelope(updated, revision=updated["revision"])


@router.patch("/loi/{defect_id}")
@router.patch("/du-an/{project_id}/loi/{defect_id}")
async def update_defect(defect_id: str, payload: dict = Body(), project_id: str | None = None, user: CurrentUser = Depends(get_current_user)):
    defect = await get_project_entity(
        "defects",
        defect_id,
        user,
        "defect.update",
        assigned_role="DEVELOPER",
        assigned_user_field="assignee",
    )
    if project_id is not None and defect["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    expected_revision = payload.get("expected_revision")
    if not isinstance(expected_revision, int):
        raise HTTPException(status_code=422, detail="Thiếu expected_revision")
    allowed = {"title", "description_doc", "steps_to_reproduce", "actual_result_doc", "expected_result_doc", "severity", "priority", "environment", "environment_id", "release", "release_id", "build", "build_id", "assignee", "attachments", "linked_test_result_id", "linked_test_case_version_id", "linked_requirement_version_ids"}
    if "assignee" in payload:
        await get_project(defect["project_id"], user, "defect.assign")
    if any(field in payload for field in {"linked_test_result_id", "linked_test_case_version_id", "linked_requirement_version_ids"}):
        await get_project(defect["project_id"], user, "defect.trace.manage", assigned_role="DEVELOPER", assigned_user_id=defect.get("assignee"))
    if "attachments" in payload:
        await get_project(defect["project_id"], user, "attachment.manage", assigned_role="DEVELOPER", assigned_user_id=defect.get("assignee"))
    if "linked_test_result_id" in payload and payload["linked_test_result_id"]:
        result = await database.value.test_results.find_one(
            {"_id": payload["linked_test_result_id"], "project_id": defect["project_id"]}
        )
        if not result or result.get("status") != "FAIL":
            raise HTTPException(status_code=422, detail={"code": "DEFECT_REQUIRES_FAILED_RESULT"})
    if "linked_test_case_version_id" in payload and payload["linked_test_case_version_id"]:
        version = await database.value.test_case_versions.find_one(
            {"_id": payload["linked_test_case_version_id"], "project_id": defect["project_id"]}
        )
        if not version:
            raise HTTPException(status_code=422, detail={"code": "INVALID_TEST_CASE_VERSION"})
    if "linked_requirement_version_ids" in payload:
        requirement_ids = list(dict.fromkeys(payload.get("linked_requirement_version_ids") or []))
        count = await database.value.requirement_versions.count_documents(
            {"project_id": defect["project_id"], "_id": {"$in": requirement_ids}}
        )
        if count != len(requirement_ids):
            raise HTTPException(status_code=422, detail={"code": "INVALID_REQUIREMENT_VERSION"})
    changes = {key: value for key, value in payload.items() if key in allowed}
    if {"release_id", "build_id", "environment_id", "release", "build", "environment"} & set(changes):
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
    updated = await optimistic_patch("defects", defect_id, defect["project_id"], expected_revision, changes)
    await audit(user.id, "defect_updated", "Defect", defect_id, defect["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/loi/{defect_id}/chuyen-trang-thai")
async def transition_defect(defect_id: str, payload: DefectTransition, user: CurrentUser = Depends(get_current_user)):
    if payload.to_status in {"CONFIRMED", "REJECTED", "DUPLICATE"}:
        permission = "defect.triage"
    elif payload.to_status in {"IN_PROGRESS", "RESOLVED"}:
        permission = "defect.transition.developer"
    elif payload.to_status in {"READY_FOR_RETEST", "REOPENED"}:
        permission = "defect.retest"
    elif payload.to_status == "CLOSED":
        permission = "defect.close"
    else:
        permission = "defect.update"
    defect = await get_project_entity(
        "defects",
        defect_id,
        user,
        permission,
        assigned_role="DEVELOPER" if permission == "defect.transition.developer" else None,
        assigned_user_field="assignee" if permission == "defect.transition.developer" else None,
    )
    if payload.to_status in {"REJECTED", "DUPLICATE"}:
        await require_action_policy(defect["project_id"], user, f"defect.{payload.to_status.lower()}", {"QA_LEAD"})
    allowed = DEFECT_TRANSITIONS.get(defect["status"], set())
    if payload.to_status not in allowed:
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION", "from": defect["status"], "to": payload.to_status})
    updated = await database.value.defects.find_one_and_update(
        {"_id": defect_id, "project_id": defect["project_id"], "status": defect["status"], "revision": payload.expected_revision},
        {"$set": {"status": payload.to_status, "transition_reason": payload.reason, "transitioned_by": user.id, "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "defect_transitioned", "Defect", defect_id, defect["project_id"], {"from": defect["status"], "to": payload.to_status, "reason": payload.reason})
    return envelope(updated, revision=updated["revision"])


@router.post("/du-an/{project_id}/loi/{defect_id}/kiem-thu-lai")
async def retest_defect(
    project_id: str,
    defect_id: str,
    payload: DefectRetestInput,
    user: CurrentUser = Depends(get_current_user),
):
    defect = await get_project_entity("defects", defect_id, user, "defect.retest")
    if defect["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    existing = await database.value.defect_retests.find_one(
        {"defect_id": defect_id, "idempotency_key": payload.idempotency_key}
    )
    if existing:
        return envelope(
            {
                "defect": await database.value.defects.find_one(
                    {"_id": defect_id, "project_id": project_id}
                ),
                "retest": existing,
            }
        )
    if defect["status"] != "READY_FOR_RETEST":
        raise HTTPException(
            status_code=409,
            detail={"code": "DEFECT_NOT_READY_FOR_RETEST", "status": defect["status"]},
        )
    result = await database.value.test_results.find_one(
        {"_id": payload.test_result_id, "project_id": project_id}
    )
    if not result:
        raise HTTPException(status_code=422, detail={"code": "INVALID_RETEST_RESULT"})
    if result.get("status") not in {"PASS", "FAIL"}:
        raise HTTPException(status_code=422, detail={"code": "RETEST_RESULT_MUST_PASS_OR_FAIL"})
    if result["status"] == "PASS":
        await get_project(project_id, user, "defect.close")
    linked_version_id = defect.get("linked_test_case_version_id")
    if linked_version_id and result.get("test_case_version_id") != linked_version_id:
        raise HTTPException(status_code=422, detail={"code": "RETEST_CASE_VERSION_MISMATCH"})
    target_status = "CLOSED" if result["status"] == "PASS" else "REOPENED"
    event = {
        "_id": new_id("DRT"),
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
        "application_status": "PENDING",
        "created_at": now(),
    }
    try:
        await database.value.defect_retests.insert_one(event)
    except DuplicateKeyError:
        existing = await database.value.defect_retests.find_one(
            {"defect_id": defect_id, "idempotency_key": payload.idempotency_key}
        )
        return envelope(
            {
                "defect": await database.value.defects.find_one(
                    {"_id": defect_id, "project_id": project_id}
                ),
                "retest": existing,
            }
        )
    updated = await database.value.defects.find_one_and_update(
        {
            "_id": defect_id,
            "project_id": project_id,
            "status": "READY_FOR_RETEST",
            "revision": payload.expected_revision,
        },
        {
            "$set": {
                "status": target_status,
                "last_retest_id": event["_id"],
                "last_retest_result_id": result["_id"],
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
            "$push": {"retest_event_ids": event["_id"]},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        await database.value.defect_retests.delete_one(
            {"_id": event["_id"], "application_status": "PENDING"}
        )
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    event["application_status"] = "APPLIED"
    await database.value.defect_retests.update_one(
        {"_id": event["_id"]}, {"$set": {"application_status": "APPLIED"}}
    )
    await audit(
        user.id,
        "defect_retested",
        "Defect",
        defect_id,
        project_id,
        {
            "test_result_id": result["_id"],
            "outcome": result["status"],
            "to": target_status,
        },
    )
    return envelope({"defect": updated, "retest": event}, revision=updated["revision"])


async def validate_test_versions(project_id, version_ids):
    count = await database.value.test_case_versions.count_documents({"project_id": project_id, "_id": {"$in": version_ids}})
    if count != len(set(version_ids)):
        raise HTTPException(status_code=422, detail={"code": "CROSS_PROJECT_OR_MISSING_TEST_VERSION"})


DEFECT_TRANSITIONS = {
    "NEW": {"CONFIRMED", "REJECTED", "DUPLICATE"},
    "CONFIRMED": {"IN_PROGRESS", "REJECTED", "DUPLICATE"},
    "IN_PROGRESS": {"RESOLVED"},
    "RESOLVED": {"READY_FOR_RETEST", "REOPENED"},
    "READY_FOR_RETEST": set(),
    "REOPENED": {"IN_PROGRESS", "RESOLVED"},
    "CLOSED": {"REOPENED"},
    "REJECTED": {"REOPENED"},
    "DUPLICATE": {"REOPENED"},
}


EXECUTION_TRANSITIONS = {
    "NOT_RUN": {"IN_PROGRESS", "SKIPPED"},
    "IN_PROGRESS": {"PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"},
    "PASS": set(),
    "FAIL": set(),
    "BLOCKED": set(),
    "SKIPPED": set(),
    "NOT_APPLICABLE": set(),
}
