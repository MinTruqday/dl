import csv
import io

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, next_key, now, optimistic_patch
from src.core.database import database
from src.domain.schemas import (
    DefectCreate,
    DefectTransition,
    TestPlanCreate,
    TestResultCorrectionInput,
    TestResultInput,
    TestRunCreate,
    TestSuiteCreate,
)
from src.services.project_rag import index_artifact


router = APIRouter(prefix="/api/qa", tags=["QA Execution"])


@router.post("/test-plans", status_code=201)
async def create_test_plan(payload: TestPlanCreate, user: CurrentUser = Depends(get_current_user)):
    await get_project(payload.project_id, user, write=True)
    timestamp = now()
    plan = {"_id": new_id("TP"), **payload.model_dump(), "status": "DRAFT", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    await database.value.test_plans.insert_one(plan)
    await audit(user.id, "test_plan_created", "TestPlan", plan["_id"], payload.project_id)
    return envelope(plan, revision=1)


@router.get("/projects/{project_id}/test-plans")
async def list_test_plans(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user)
    return envelope(await database.value.test_plans.find({"project_id": project_id}).sort("updated_at", -1).to_list(500))


@router.post("/test-suites", status_code=201)
async def create_test_suite(payload: TestSuiteCreate, user: CurrentUser = Depends(get_current_user)):
    await get_project(payload.project_id, user, write=True)
    await validate_test_versions(payload.project_id, payload.test_case_version_ids)
    timestamp = now()
    suite = {"_id": new_id("TSU"), **payload.model_dump(), "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    await database.value.test_suites.insert_one(suite)
    await audit(user.id, "test_suite_created", "TestSuite", suite["_id"], payload.project_id)
    return envelope(suite, revision=1)


@router.get("/projects/{project_id}/test-suites")
async def list_test_suites(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user)
    return envelope(await database.value.test_suites.find({"project_id": project_id}).sort("updated_at", -1).to_list(500))


@router.post("/test-runs", status_code=201)
async def create_test_run(payload: TestRunCreate, user: CurrentUser = Depends(get_current_user)):
    await get_project(payload.project_id, user, write=True)
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
    await audit(user.id, "test_run_created", "TestRun", run["_id"], payload.project_id, {"test_count": len(version_ids)})
    return envelope(run, revision=1)


@router.get("/projects/{project_id}/test-runs")
async def list_test_runs(
    project_id: str,
    status: str = Query(default="", max_length=30),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user)
    query = {"project_id": project_id}
    if status:
        query["status"] = status
    return envelope(await database.value.test_runs.find(query).sort("updated_at", -1).to_list(500))


@router.get("/test-runs/{run_id}")
async def get_test_run(run_id: str, user: CurrentUser = Depends(get_current_user)):
    run = await get_project_entity("test_runs", run_id, user)
    versions = await database.value.test_case_versions.find({"_id": {"$in": run["test_case_version_ids"]}}).to_list(10000)
    results = await database.value.test_results.find({"test_run_id": run_id}).to_list(10000)
    defects = await database.value.defects.find({"project_id": run["project_id"], "linked_test_result_id": {"$in": [item["_id"] for item in results]}}).to_list(10000)
    return envelope({**run, "test_case_versions": versions, "results": results, "defects": defects})


@router.get("/test-runs/{run_id}/report")
async def export_test_run_report(run_id: str, user: CurrentUser = Depends(get_current_user)):
    run = await get_project_entity("test_runs", run_id, user)
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
    run = await get_project_entity("test_runs", run_id, user, write=True)
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
    run = await get_project_entity("test_runs", run_id, user, write=True)
    if run["status"] != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail={"code": "TEST_RUN_NOT_IN_PROGRESS"})
    if test_case_version_id not in run["test_case_version_ids"]:
        raise HTTPException(status_code=422, detail={"code": "TEST_NOT_IN_RUN_SNAPSHOT"})
    existing = await database.value.test_results.find_one({"test_run_id": run_id, "test_case_version_id": test_case_version_id})
    if existing:
        if existing.get("idempotency_key") == payload.idempotency_key:
            return envelope(existing)
        raise HTTPException(status_code=409, detail={"code": "RESULT_ALREADY_RECORDED"})
    result = {"_id": new_id("TRES"), "project_id": run["project_id"], "test_run_id": run_id, "test_case_version_id": test_case_version_id, **payload.model_dump(), "executed_by": user.id, "executed_at": now(), "created_at": now()}
    await database.value.test_results.insert_one(result)
    await database.value.test_runs.update_one({"_id": run_id}, {"$set": {"updated_at": now()}, "$inc": {"revision": 1}})
    await audit(user.id, "test_result_recorded", "TestResult", result["_id"], run["project_id"], {"status": payload.status})
    return envelope(result)


@router.post("/test-results/{result_id}/corrections")
async def correct_test_result(result_id: str, payload: TestResultCorrectionInput, user: CurrentUser = Depends(get_current_user)):
    result = await get_project_entity("test_results", result_id, user, write=True)
    existing = await database.value.test_result_corrections.find_one({"test_result_id": result_id, "idempotency_key": payload.idempotency_key})
    if existing:
        return envelope({"result": await database.value.test_results.find_one({"_id": result_id}), "correction": existing})
    event = {"_id": new_id("TRC"), "project_id": result["project_id"], "test_result_id": result_id, "from_status": result.get("status"), "to_status": payload.status, "reason": payload.reason, "idempotency_key": payload.idempotency_key, "corrected_by": user.id, "created_at": now()}
    await database.value.test_result_corrections.insert_one(event)
    await database.value.test_results.update_one({"_id": result_id}, {"$set": {"status": payload.status, "corrected": True, "last_correction_id": event["_id"], "updated_at": now()}, "$push": {"correction_event_ids": event["_id"]}})
    await audit(user.id, "test_result_corrected", "TestResult", result_id, result["project_id"], {"from": result.get("status"), "to": payload.status, "correction_id": event["_id"]})
    return envelope({"result": await database.value.test_results.find_one({"_id": result_id}), "correction": event})


@router.post("/test-runs/{run_id}/complete")
async def complete_test_run(run_id: str, user: CurrentUser = Depends(get_current_user)):
    run = await get_project_entity("test_runs", run_id, user, write=True)
    if run["status"] == "COMPLETED":
        return envelope(run)
    if run["status"] != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    result_count = await database.value.test_results.count_documents({"test_run_id": run_id})
    if result_count < len(run["test_case_version_ids"]):
        raise HTTPException(status_code=409, detail={"code": "PARTIAL_EXECUTION", "completed": result_count, "total": len(run["test_case_version_ids"])})
    await database.value.test_runs.update_one({"_id": run_id}, {"$set": {"status": "COMPLETED", "completed_at": now(), "completed_by": user.id, "updated_at": now()}, "$inc": {"revision": 1}})
    await audit(user.id, "test_run_completed", "TestRun", run_id, run["project_id"])
    return envelope(await database.value.test_runs.find_one({"_id": run_id}))


@router.post("/test-runs/{run_id}/abort")
async def abort_test_run(run_id: str, reason: str = Body(embed=True, min_length=2, max_length=2000), user: CurrentUser = Depends(get_current_user)):
    run = await get_project_entity("test_runs", run_id, user, write=True)
    if run["status"] not in {"DRAFT", "READY", "IN_PROGRESS"}:
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    await database.value.test_runs.update_one({"_id": run_id}, {"$set": {"status": "ABORTED", "abort_reason": reason, "aborted_by": user.id, "aborted_at": now(), "updated_at": now()}, "$inc": {"revision": 1}})
    await audit(user.id, "test_run_aborted", "TestRun", run_id, run["project_id"], {"reason": reason})
    return envelope(await database.value.test_runs.find_one({"_id": run_id}))


@router.post("/projects/{project_id}/defects", status_code=201)
async def create_defect(project_id: str, payload: DefectCreate, user: CurrentUser = Depends(get_current_user)):
    if project_id != payload.project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    await get_project(project_id, user, write=True)
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
    status: str = Query(default="", max_length=40),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user)
    query = {"project_id": project_id}
    if status:
        query["status"] = status
    return envelope(await database.value.defects.find(query).sort("updated_at", -1).to_list(1000))


@router.patch("/defects/{defect_id}")
async def update_defect(defect_id: str, payload: dict = Body(), user: CurrentUser = Depends(get_current_user)):
    defect = await get_project_entity("defects", defect_id, user, write=True)
    expected_revision = payload.get("expected_revision")
    if not isinstance(expected_revision, int):
        raise HTTPException(status_code=422, detail="Thiếu expected_revision")
    allowed = {"title", "description_doc", "steps_to_reproduce", "actual_result_doc", "expected_result_doc", "severity", "priority", "environment", "build", "assignee", "attachments"}
    updated = await optimistic_patch("defects", defect_id, defect["project_id"], expected_revision, {key: value for key, value in payload.items() if key in allowed})
    await audit(user.id, "defect_updated", "Defect", defect_id, defect["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/defects/{defect_id}/transition")
async def transition_defect(defect_id: str, payload: DefectTransition, user: CurrentUser = Depends(get_current_user)):
    defect = await get_project_entity("defects", defect_id, user, write=True)
    allowed = DEFECT_TRANSITIONS.get(defect["status"], set())
    if payload.to_status not in allowed:
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION", "from": defect["status"], "to": payload.to_status})
    await database.value.defects.update_one({"_id": defect_id}, {"$set": {"status": payload.to_status, "transition_reason": payload.reason, "transitioned_by": user.id, "updated_at": now()}, "$inc": {"revision": 1}})
    await audit(user.id, "defect_transitioned", "Defect", defect_id, defect["project_id"], {"from": defect["status"], "to": payload.to_status, "reason": payload.reason})
    return envelope(await database.value.defects.find_one({"_id": defect_id}))


@router.get("/projects/{project_id}/defects/export")
async def export_defects(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user)
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
    "READY_FOR_RETEST": {"CLOSED", "REOPENED"},
    "REOPENED": {"IN_PROGRESS", "RESOLVED"},
    "CLOSED": {"REOPENED"},
    "REJECTED": {"REOPENED"},
    "DUPLICATE": {"REOPENED"},
}
