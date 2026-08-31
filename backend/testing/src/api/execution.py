import csv
import io
import re
from difflib import SequenceMatcher

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, next_key, now, optimistic_patch, page_payload, plain_text, require_action_policy, sort_spec
from src.core.database import database
from src.domain.schemas import (
    DefectCreate,
    DefectRetestInput,
    DefectTransition,
    TestExecutionPatch,
    TestPlanCreate,
    TestPlanPatch,
    TestResultCorrectionInput,
    TestResultInput,
    TestRunCreate,
    TestRunAssignmentInput,
    TestRunPatch,
    TestSuiteCreate,
    TestSuitePatch,
    ProjectArchiveInput,
    ReviewTransitionInput,
)
from src.services.project_knowledge import index_artifact


router = APIRouter(prefix="/api/qa", tags=["QA Execution"])


@router.post("/test-plans", status_code=201)
@router.post("/projects/{project_id}/test-plans", status_code=201)
async def create_test_plan(payload: TestPlanCreate, project_id: str | None = None, user: CurrentUser = Depends(get_current_user)):
    if project_id and project_id != payload.project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_SCOPE_MISMATCH"})
    await get_project(payload.project_id, user, "testplan.create")
    if payload.members:
        await require_action_policy(
            payload.project_id, user, "testplan.assignments", {"QA_LEAD"}
        )
    timestamp = now()
    plan = {"_id": new_id("TP"), **payload.model_dump(), "status": "DRAFT", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    await database.value.test_plans.insert_one(plan)
    await audit(user.id, "test_plan_created", "TestPlan", plan["_id"], payload.project_id)
    return envelope(plan, revision=1)


@router.get("/projects/{project_id}/test-plans")
async def list_test_plans(
    project_id: str,
    q: str = Query(default="", max_length=300),
    release: str = Query(default="", max_length=200),
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
    for field, value in {"release": release, "status": status}.items():
        if value:
            query[field] = value
    sort_field, direction = sort_spec(
        sort, {"name", "release", "status", "created_at", "updated_at"}
    )
    return envelope(await database.value.test_plans.find(query).sort(sort_field, direction).to_list(500))


@router.get("/test-plans/{plan_id}")
async def get_test_plan(plan_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(await get_project_entity("test_plans", plan_id, user, "testplan.read"))


@router.patch("/test-plans/{plan_id}")
async def update_test_plan(plan_id: str, payload: TestPlanPatch, user: CurrentUser = Depends(get_current_user)):
    plan = await get_project_entity("test_plans", plan_id, user, "testplan.update")
    if plan.get("status") != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "TEST_PLAN_NOT_DRAFT"})
    if payload.members is not None:
        await require_action_policy(
            plan["project_id"], user, "testplan.assignments", {"QA_LEAD"}
        )
    updated = await optimistic_patch("test_plans", plan_id, plan["project_id"], payload.expected_revision, payload.model_dump())
    await audit(user.id, "test_plan_updated", "TestPlan", plan_id, plan["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/test-plans/{plan_id}/submit-review")
async def submit_test_plan(plan_id: str, payload: ReviewTransitionInput, user: CurrentUser = Depends(get_current_user)):
    plan = await get_project_entity("test_plans", plan_id, user, "testplan.submit_review")
    if plan.get("status") != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    updated = await optimistic_patch("test_plans", plan_id, plan["project_id"], payload.expected_revision, {"status": "IN_REVIEW", "review_note": payload.review_note})
    await audit(user.id, "test_plan_submitted", "TestPlan", plan_id, plan["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/test-plans/{plan_id}/approve")
async def approve_test_plan(plan_id: str, payload: ReviewTransitionInput, user: CurrentUser = Depends(get_current_user)):
    plan = await get_project_entity("test_plans", plan_id, user, "testplan.approve")
    if plan.get("status") not in {"DRAFT", "IN_REVIEW"}:
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    updated = await optimistic_patch("test_plans", plan_id, plan["project_id"], payload.expected_revision, {"status": "APPROVED", "approved_by": user.id, "approved_at": now(), "review_note": payload.review_note})
    await audit(user.id, "test_plan_approved", "TestPlan", plan_id, plan["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/test-plans/{plan_id}/archive")
async def archive_test_plan(plan_id: str, payload: ProjectArchiveInput, user: CurrentUser = Depends(get_current_user)):
    plan = await get_project_entity("test_plans", plan_id, user, "testplan.archive")
    updated = await optimistic_patch("test_plans", plan_id, plan["project_id"], payload.expected_revision, {"status": "ARCHIVED", "archive_reason": payload.reason, "archived_by": user.id, "archived_at": now()})
    await audit(user.id, "test_plan_archived", "TestPlan", plan_id, plan["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/test-plans/{plan_id}/clone", status_code=201)
async def clone_test_plan(plan_id: str, user: CurrentUser = Depends(get_current_user)):
    plan = await get_project_entity("test_plans", plan_id, user, "testplan.create")
    timestamp = now()
    cloned = {**plan, "_id": new_id("TP"), "name": f"{plan['name']} bản sao", "status": "DRAFT", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    for field in ["approved_at", "approved_by", "archived_at", "archived_by", "archive_reason", "reviewed_at", "reviewed_by"]:
        cloned.pop(field, None)
    await database.value.test_plans.insert_one(cloned)
    await audit(user.id, "test_plan_cloned", "TestPlan", cloned["_id"], plan["project_id"], {"source_plan_id": plan_id})
    return envelope(cloned, revision=1)


@router.post("/test-suites", status_code=201)
@router.post("/projects/{project_id}/test-suites", status_code=201)
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


@router.get("/projects/{project_id}/test-suites")
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


@router.get("/test-suites/{suite_id}")
async def get_test_suite(suite_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(await get_project_entity("test_suites", suite_id, user, "testsuite.read"))


@router.patch("/test-suites/{suite_id}")
async def update_test_suite(suite_id: str, payload: TestSuitePatch, user: CurrentUser = Depends(get_current_user)):
    suite = await get_project_entity("test_suites", suite_id, user, "testsuite.update")
    if suite.get("status", "ACTIVE") == "ARCHIVED":
        raise HTTPException(status_code=409, detail={"code": "TEST_SUITE_ARCHIVED"})
    if payload.test_case_version_ids is not None:
        await validate_test_versions(suite["project_id"], payload.test_case_version_ids)
    updated = await optimistic_patch("test_suites", suite_id, suite["project_id"], payload.expected_revision, payload.model_dump())
    await audit(user.id, "test_suite_updated", "TestSuite", suite_id, suite["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/test-suites/{suite_id}/clone", status_code=201)
async def clone_test_suite(suite_id: str, user: CurrentUser = Depends(get_current_user)):
    suite = await get_project_entity("test_suites", suite_id, user, "testsuite.clone")
    timestamp = now()
    cloned = {**suite, "_id": new_id("TSU"), "name": f"{suite['name']} bản sao", "status": "ACTIVE", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    for field in ["archived_at", "archived_by", "archive_reason"]:
        cloned.pop(field, None)
    await database.value.test_suites.insert_one(cloned)
    await audit(user.id, "test_suite_cloned", "TestSuite", cloned["_id"], suite["project_id"], {"source_suite_id": suite_id})
    return envelope(cloned, revision=1)


@router.post("/test-suites/{suite_id}/archive")
async def archive_test_suite(suite_id: str, payload: ProjectArchiveInput, user: CurrentUser = Depends(get_current_user)):
    suite = await get_project_entity("test_suites", suite_id, user, "testsuite.archive")
    updated = await optimistic_patch("test_suites", suite_id, suite["project_id"], payload.expected_revision, {"status": "ARCHIVED", "archive_reason": payload.reason, "archived_by": user.id, "archived_at": now()})
    await audit(user.id, "test_suite_archived", "TestSuite", suite_id, suite["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/test-runs", status_code=201)
@router.post("/projects/{project_id}/test-runs", status_code=201)
async def create_test_run(payload: TestRunCreate, project_id: str | None = None, user: CurrentUser = Depends(get_current_user)):
    if project_id is not None and payload.project_id != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    await get_project(payload.project_id, user, "testrun.create")
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
    run = {"_id": new_id("TRUN"), **payload.model_dump(), "test_case_version_ids": version_ids, "status": "DRAFT", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
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
                        "environment": payload.environment,
                        "build": payload.build,
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


@router.patch("/projects/{project_id}/test-runs/{run_id}")
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
    updated = await optimistic_patch("test_runs", run_id, project_id, payload.expected_revision, changes)
    await audit(user.id, "test_run_updated", "TestRun", run_id, project_id)
    return envelope(updated, revision=updated["revision"])


@router.post("/projects/{project_id}/test-runs/{run_id}/assign")
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


@router.get("/projects/{project_id}/test-runs")
async def list_test_runs(
    project_id: str,
    name: str = Query(default="", max_length=300),
    release: str = Query(default="", max_length=200),
    build: str = Query(default="", max_length=200),
    environment: str = Query(default="", max_length=200),
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
        "build": build,
        "environment": environment,
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


@router.get("/projects/{project_id}/test-results")
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


@router.get("/test-runs/{run_id}")
async def get_test_run(run_id: str, user: CurrentUser = Depends(get_current_user)):
    run = await get_project_entity("test_runs", run_id, user, "testrun.read")
    versions = await database.value.test_case_versions.find({"_id": {"$in": run["test_case_version_ids"]}}).to_list(10000)
    results = await database.value.test_results.find({"test_run_id": run_id}).to_list(10000)
    defects = await database.value.defects.find({"project_id": run["project_id"], "linked_test_result_id": {"$in": [item["_id"] for item in results]}}).to_list(10000)
    return envelope({**run, "test_case_versions": versions, "results": results, "defects": defects})


@router.get("/test-runs/{run_id}/report")
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


@router.post("/test-runs/{run_id}/start")
async def start_test_run(run_id: str, user: CurrentUser = Depends(get_current_user)):
    run = await get_project_entity("test_runs", run_id, user, "testrun.start")
    if run["status"] == "IN_PROGRESS":
        return envelope(run)
    if run["status"] not in {"DRAFT", "READY"}:
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    await database.value.test_runs.update_one({"_id": run_id}, {"$set": {"status": "IN_PROGRESS", "started_at": now(), "started_by": user.id, "updated_at": now()}, "$inc": {"revision": 1}})
    await audit(user.id, "test_run_started", "TestRun", run_id, run["project_id"])
    return envelope(await database.value.test_runs.find_one({"_id": run_id}))


@router.post("/test-runs/{run_id}/results/{test_case_version_id}")
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


@router.patch("/projects/{project_id}/test-executions/{execution_id}")
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


@router.post("/test-results/{result_id}/corrections")
async def correct_test_result(result_id: str, payload: TestResultCorrectionInput, user: CurrentUser = Depends(get_current_user)):
    result = await get_project_entity(
        "test_results", result_id, user, "testresult.correct"
    )
    existing = await database.value.test_result_corrections.find_one({"test_result_id": result_id, "idempotency_key": payload.idempotency_key})
    if existing:
        return envelope({"result": await database.value.test_results.find_one({"_id": result_id}), "correction": existing})
    event = {"_id": new_id("TRC"), "project_id": result["project_id"], "test_result_id": result_id, "from_status": result.get("status"), "to_status": payload.status, "reason": payload.reason, "idempotency_key": payload.idempotency_key, "corrected_by": user.id, "created_at": now()}
    try:
        await database.value.test_result_corrections.insert_one(event)
    except DuplicateKeyError:
        event = await database.value.test_result_corrections.find_one({"test_result_id": result_id, "idempotency_key": payload.idempotency_key})
        return envelope({"result": await database.value.test_results.find_one({"_id": result_id}), "correction": event})
    await database.value.test_results.update_one({"_id": result_id}, {"$set": {"status": payload.status, "corrected": True, "last_correction_id": event["_id"], "completed_at": now(), "updated_at": now()}, "$push": {"correction_event_ids": event["_id"]}, "$inc": {"revision": 1}})
    await audit(user.id, "test_result_corrected", "TestResult", result_id, result["project_id"], {"from": result.get("status"), "to": payload.status, "correction_id": event["_id"]})
    return envelope({"result": await database.value.test_results.find_one({"_id": result_id}), "correction": event})


@router.post("/test-runs/{run_id}/complete")
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


@router.post("/test-runs/{run_id}/abort")
async def abort_test_run(run_id: str, reason: str = Body(embed=True, min_length=2, max_length=2000), user: CurrentUser = Depends(get_current_user)):
    run = await get_project_entity("test_runs", run_id, user, "testrun.abort")
    if run["status"] not in {"DRAFT", "READY", "IN_PROGRESS"}:
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    await database.value.test_runs.update_one({"_id": run_id}, {"$set": {"status": "ABORTED", "abort_reason": reason, "aborted_by": user.id, "aborted_at": now(), "updated_at": now()}, "$inc": {"revision": 1}})
    await audit(user.id, "test_run_aborted", "TestRun", run_id, run["project_id"], {"reason": reason})
    return envelope(await database.value.test_runs.find_one({"_id": run_id}))


@router.post("/projects/{project_id}/defects", status_code=201)
async def create_defect(project_id: str, payload: DefectCreate, user: CurrentUser = Depends(get_current_user)):
    if project_id != payload.project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    await get_project(project_id, user, "defect.create")
    if payload.linked_test_result_id:
        result = await database.value.test_results.find_one({"_id": payload.linked_test_result_id, "project_id": project_id})
        if not result or result["status"] != "FAIL":
            raise HTTPException(status_code=422, detail={"code": "DEFECT_REQUIRES_FAILED_RESULT"})
    timestamp = now()
    defect = {"_id": new_id("DEF"), **payload.model_dump(), "defect_key": payload.defect_key or await next_key(project_id, "defect", "DEF"), "status": "NEW", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    await database.value.defects.insert_one(defect)
    await index_artifact(project_id, "defect", defect["_id"], defect["_id"], defect["title"], " ".join([defect["title"], str(payload.environment), str(payload.build)]), defect["status"], "record", 1)
    await audit(user.id, "defect_created", "Defect", defect["_id"], project_id)
    return envelope(defect, revision=1)


@router.get("/projects/{project_id}/defects")
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
    environment: str = Query(default="", max_length=500),
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
        "environment": environment,
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
        {"defect_key", "title", "status", "severity", "priority", "assignee", "release", "environment", "created_at", "updated_at"},
    )
    total = await database.value.defects.count_documents(query)
    items = await database.value.defects.find(query).sort(sort_field, direction).skip(
        (page - 1) * page_size
    ).limit(page_size).to_list(page_size)
    return envelope(page_payload(items, page, page_size, total))


@router.get("/projects/{project_id}/defects/duplicates")
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


@router.get("/defects/{defect_id}/trace-candidates")
async def find_defect_trace_candidates(
    defect_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    defect = await get_project_entity("defects", defect_id, user, "defect.read")
    text = " ".join(
        [
            defect.get("title", ""),
            plain_text(defect.get("description_doc", {})),
            plain_text(defect.get("actual_result_doc", {})),
            plain_text(defect.get("expected_result_doc", {})),
        ]
    ).lower()
    test_cases = await database.value.test_cases.find(
        {"project_id": defect["project_id"], "status": {"$ne": "OBSOLETE"}}
    ).to_list(2000)
    current_ids = [item.get("current_version_id") for item in test_cases if item.get("current_version_id")]
    versions = await database.value.test_case_versions.find(
        {"project_id": defect["project_id"], "_id": {"$in": current_ids}}
    ).to_list(2000)
    linked_requirements = set(defect.get("linked_requirement_version_ids", []))
    candidates = []
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
        candidates.append(
            {
                "_id": version["_id"],
                "test_case_id": version["test_case_id"],
                "test_case_version_id": version["_id"],
                "test_case_key": version["test_case_key"],
                "title": version["title"],
                "requirement_version_ids": version.get("requirement_version_ids", []),
                "confidence": round(score, 4),
                "confidence_band": "HIGH" if score >= 0.75 else "MEDIUM" if score >= 0.5 else "LOW",
                "reason_codes": reasons,
                "evidence": [
                    {"artifact_type": "defect", "artifact_id": defect_id},
                    {"artifact_type": "test_case_version", "artifact_id": version["_id"]},
                ],
            }
        )
    candidates.sort(key=lambda item: item["confidence"], reverse=True)
    return envelope(candidates[:50])


@router.patch("/defects/{defect_id}")
@router.patch("/projects/{project_id}/defects/{defect_id}")
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
    allowed = {"title", "description_doc", "steps_to_reproduce", "actual_result_doc", "expected_result_doc", "severity", "priority", "environment", "release", "build", "assignee", "attachments", "linked_test_result_id", "linked_test_case_version_id", "linked_requirement_version_ids"}
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
    updated = await optimistic_patch("defects", defect_id, defect["project_id"], expected_revision, {key: value for key, value in payload.items() if key in allowed})
    await audit(user.id, "defect_updated", "Defect", defect_id, defect["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/defects/{defect_id}/transition")
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


@router.post("/projects/{project_id}/defects/{defect_id}/retest")
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


@router.get("/projects/{project_id}/defects/export")
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
