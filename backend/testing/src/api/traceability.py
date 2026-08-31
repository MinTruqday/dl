import csv
import io

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.database import database
from src.core.metrics import STALE, TRACE_ACCEPTANCE_RATE, UNCOVERED
from src.domain.schemas import TraceLinkCreate


router = APIRouter(prefix="/api/qa", tags=["QA Traceability"])


@router.post("/trace-links", status_code=201)
@router.post("/projects/{project_id}/trace-links", status_code=201)
async def create_trace_link(
    payload: TraceLinkCreate,
    project_id: str | None = None,
    user: CurrentUser = Depends(get_current_user),
):
    if project_id is not None and payload.project_id != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    await get_project(payload.project_id, user, "trace.create")
    await validate_artifact(payload.source_type, payload.source_id, payload.project_id)
    await validate_artifact(payload.target_type, payload.target_id, payload.project_id)
    existing = await database.value.trace_links.find_one(
        {
            "project_id": payload.project_id,
            "source_type": payload.source_type,
            "source_id": payload.source_id,
            "target_type": payload.target_type,
            "target_id": payload.target_id,
            "link_type": payload.link_type,
        }
    )
    if existing:
        return envelope(existing)
    link = {
        "_id": new_id("TL"),
        **payload.model_dump(),
        "status": "CONFIRMED" if payload.origin == "manual" else "SUGGESTED",
        "revision": 1,
        "created_by": user.id,
        "created_at": now(),
        "updated_at": now(),
    }
    try:
        await database.value.trace_links.insert_one(link)
    except DuplicateKeyError:
        existing = await database.value.trace_links.find_one(
            {
                "project_id": payload.project_id,
                "source_type": payload.source_type,
                "source_id": payload.source_id,
                "target_type": payload.target_type,
                "target_id": payload.target_id,
                "link_type": payload.link_type,
            }
        )
        return envelope(existing)
    await audit(user.id, "trace_link_created", "TraceLink", link["_id"], payload.project_id)
    return envelope(link)


@router.post("/trace-links/{link_id}/confirm")
@router.post("/projects/{project_id}/trace-links/{link_id}/confirm")
async def confirm_trace_link(link_id: str, project_id: str | None = None, user: CurrentUser = Depends(get_current_user)):
    if project_id is not None:
        link = await get_project_entity("trace_links", link_id, user, "trace.confirm")
        if link["project_id"] != project_id:
            raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    return await review_link(link_id, "CONFIRMED", user)


@router.post("/trace-links/{link_id}/reject")
@router.post("/projects/{project_id}/trace-links/{link_id}/reject")
async def reject_trace_link(link_id: str, project_id: str | None = None, user: CurrentUser = Depends(get_current_user)):
    if project_id is not None:
        link = await get_project_entity("trace_links", link_id, user, "trace.review")
        if link["project_id"] != project_id:
            raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    return await review_link(link_id, "REJECTED", user)


@router.delete("/trace-links/{link_id}")
@router.delete("/projects/{project_id}/trace-links/{link_id}")
async def revoke_trace_link(link_id: str, project_id: str | None = None, user: CurrentUser = Depends(get_current_user)):
    link = await get_project_entity("trace_links", link_id, user, "trace.revoke")
    if project_id is not None and link["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    if link.get("status") == "REVOKED":
        return envelope(link)
    if link.get("status") not in {"CONFIRMED", "SUGGESTED"}:
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    updated = await database.value.trace_links.find_one_and_update(
        {"_id": link_id, "project_id": link["project_id"], "status": link["status"]},
        {"$set": {"status": "REVOKED", "revoked_by": user.id, "revoked_at": now(), "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "TRACE_DECISION_CONFLICT"})
    link = updated
    await audit(user.id, "trace_link_revoked", "TraceLink", link_id, link["project_id"])
    return envelope(link)


async def review_link(link_id, status, user):
    permission = "trace.confirm" if status == "CONFIRMED" else "trace.review"
    link = await get_project_entity("trace_links", link_id, user, permission)
    if link.get("status") == status:
        return envelope(link)
    if link.get("status") != "SUGGESTED":
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    updated = await database.value.trace_links.find_one_and_update(
        {"_id": link_id, "project_id": link["project_id"], "status": "SUGGESTED"},
        {"$set": {"status": status, "reviewed_by": user.id, "reviewed_at": now(), "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "TRACE_DECISION_CONFLICT"})
    link = updated
    reviewed = await database.value.trace_links.count_documents({"project_id": link["project_id"], "status": {"$in": ["CONFIRMED", "REJECTED"]}})
    confirmed = await database.value.trace_links.count_documents({"project_id": link["project_id"], "status": "CONFIRMED"})
    TRACE_ACCEPTANCE_RATE.set(confirmed / reviewed if reviewed else 0)
    await audit(user.id, f"trace_link_{status.lower()}", "TraceLink", link_id, link["project_id"])
    return envelope(link)


@router.get("/projects/{project_id}/traceability")
async def traceability(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "trace.read")
    requirements = await database.value.requirements.find({"project_id": project_id}).sort("requirement_key", 1).to_list(5000)
    versions = await database.value.requirement_versions.find({"_id": {"$in": [item["current_version_id"] for item in requirements]}}).to_list(5000)
    criteria = await database.value.acceptance_criteria.find({"project_id": project_id}).to_list(10000)
    tests = await database.value.test_cases.find({"project_id": project_id}).sort("test_case_key", 1).to_list(10000)
    test_versions = await database.value.test_case_versions.find({"_id": {"$in": [item["current_version_id"] for item in tests if item.get("current_version_id")]}}).to_list(10000)
    defects = await database.value.defects.find(
        {
            "project_id": project_id,
            "status": {"$nin": ["CLOSED", "REJECTED", "DUPLICATE"]},
        }
    ).to_list(20000)
    links = await database.value.trace_links.find({"project_id": project_id}).to_list(50000)
    obsolete_requirement_ids = {
        item["_id"] for item in requirements if item.get("status") == "OBSOLETE"
    }
    obsolete_requirement_versions = await database.value.requirement_versions.find(
        {"project_id": project_id, "requirement_id": {"$in": list(obsolete_requirement_ids)}}
    ).to_list(10000)
    obsolete_requirement_version_ids = {
        item["_id"] for item in obsolete_requirement_versions
    }
    obsolete_criterion_ids = {
        item["_id"]
        for item in criteria
        if item.get("requirement_version_id") in obsolete_requirement_version_ids
    }
    obsolete_test_ids = {item["_id"] for item in tests if item.get("status") == "OBSOLETE"}
    obsolete_test_versions = await database.value.test_case_versions.find(
        {"project_id": project_id, "test_case_id": {"$in": list(obsolete_test_ids)}}
    ).to_list(20000)
    obsolete_test_version_ids = {item["_id"] for item in obsolete_test_versions}
    enriched_links = []
    for link in links:
        reasons = []
        if link.get("source_id") in obsolete_requirement_version_ids | obsolete_criterion_ids:
            reasons.append("OBSOLETE_SOURCE")
        if link.get("target_id") in obsolete_test_version_ids:
            reasons.append("OBSOLETE_TARGET")
        enriched_links.append({**link, "obsolete": bool(reasons), "obsolete_reasons": reasons})
    return envelope({"requirements": requirements, "requirement_versions": versions, "acceptance_criteria": criteria, "test_cases": tests, "test_case_versions": test_versions, "trace_links": enriched_links, "defects": defects})


@router.get("/projects/{project_id}/coverage")
async def coverage(
    project_id: str,
    build: str = Query(default="", max_length=200),
    release: str = Query(default="", max_length=200),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "coverage.read")
    requirements = await database.value.requirements.find({"project_id": project_id, "status": "BASELINED"}).to_list(10000)
    requirement_versions = {item["current_version_id"] for item in requirements}
    criteria = await database.value.acceptance_criteria.find({"project_id": project_id, "requirement_version_id": {"$in": list(requirement_versions)}, "status": {"$ne": "obsolete"}}).to_list(20000)
    links = await database.value.trace_links.find({"project_id": project_id, "status": "CONFIRMED"}).to_list(50000)
    test_version_ids = {link["target_id"] for link in links if link["target_type"] == "test_case_version"}
    test_versions = await database.value.test_case_versions.find({"_id": {"$in": list(test_version_ids)}}).to_list(50000)
    linked_requirements = {link["source_id"] for link in links if link["source_type"] == "requirement_version"}
    linked_criteria = {link["source_id"] for link in links if link["source_type"] == "acceptance_criterion"}
    requirement_coverage = percent(len(requirement_versions & linked_requirements), len(requirement_versions))
    criterion_ids = {item["_id"] for item in criteria}
    criterion_coverage = percent(len(criterion_ids & linked_criteria), len(criterion_ids))
    categories = {}
    for category in ("happy_path", "negative", "boundary", "permission"):
        covered_sources = set()
        category_versions = {item["_id"] for item in test_versions if item.get("type") == category}
        for link in links:
            if link["target_id"] in category_versions:
                covered_sources.add(link["source_id"])
        categories[category] = percent(len(requirement_versions & covered_sources), len(requirement_versions))
    uncovered = [item for item in requirements if item["current_version_id"] not in linked_requirements]
    unlinked_tests = await database.value.test_cases.find({"project_id": project_id, "current_version_id": {"$nin": list(test_version_ids)}}).to_list(10000)
    stale_tests = await database.value.test_cases.count_documents({"project_id": project_id, "status": "NEEDS_UPDATE"})
    active_tests = await database.value.test_cases.find({"project_id": project_id, "status": "ACTIVE"}).to_list(20000)
    active_version_ids = {item.get("current_version_id") for item in active_tests if item.get("current_version_id")}
    fresh_requirement_ids = {
        link["source_id"]
        for link in links
        if link.get("source_type") == "requirement_version" and link.get("target_id") in active_version_ids
    }
    fresh_coverage = percent(len(requirement_versions & fresh_requirement_ids), len(requirement_versions))
    run_query = {"project_id": project_id}
    if build:
        run_query["build"] = build
    if release:
        plans = await database.value.test_plans.find({"project_id": project_id, "release": release}, {"_id": 1}).to_list(5000)
        run_query["test_plan_id"] = {"$in": [item["_id"] for item in plans]}
    runs = await database.value.test_runs.find(run_query).to_list(10000)
    run_ids = [item["_id"] for item in runs]
    execution_scope_ids = {version_id for item in runs for version_id in item.get("test_case_version_ids", [])}
    terminal_results = await database.value.test_results.find({"project_id": project_id, "test_run_id": {"$in": run_ids}, "status": {"$in": ["PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"]}}).sort("completed_at", -1).to_list(50000)
    executed_version_ids = {item["test_case_version_id"] for item in terminal_results}
    execution_coverage = percent(len(execution_scope_ids & executed_version_ids), len(execution_scope_ids))
    latest_execution = {}
    for item in terminal_results:
        latest_execution.setdefault(item["test_case_version_id"], item)
    UNCOVERED.set(len(uncovered))
    STALE.set(stale_tests)
    return envelope({"requirement_coverage": requirement_coverage, "acceptance_criterion_coverage": criterion_coverage, "fresh_coverage": fresh_coverage, "execution_coverage": execution_coverage, "category_coverage": categories, "uncovered_requirements": uncovered, "unlinked_tests": unlinked_tests, "stale_tests": stale_tests, "latest_execution": latest_execution, "scope": {"build": build or None, "release": release or None, "test_case_version_ids": sorted(execution_scope_ids)}})


@router.get("/requirements/{requirement_id}/coverage")
async def requirement_coverage(requirement_id: str, user: CurrentUser = Depends(get_current_user)):
    requirement = await get_project_entity("requirements", requirement_id, user, "coverage.read")
    versions = await database.value.requirement_versions.find({"requirement_id": requirement_id, "project_id": requirement["project_id"]}).sort("version", 1).to_list(500)
    links = await database.value.trace_links.find({"project_id": requirement["project_id"], "source_type": "requirement_version", "source_id": {"$in": [item["_id"] for item in versions]}}).to_list(5000)
    return envelope({"requirement_id": requirement_id, "versions": versions, "trace_links": links, "covered": any(item.get("status") == "CONFIRMED" for item in links)})


@router.get("/projects/{project_id}/coverage-snapshots")
async def list_coverage_snapshots(
    project_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "coverage.read")
    return envelope(await database.value.coverage_snapshots.find({"project_id": project_id}).sort("created_at", -1).to_list(limit))


@router.post("/projects/{project_id}/coverage-snapshots", status_code=201)
async def create_coverage_snapshot(
    project_id: str,
    payload: dict = Body(default={}),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "coverage.snapshot.create")
    idempotency_key = str(payload.get("idempotency_key") or "").strip() or None
    if idempotency_key:
        existing = await database.value.coverage_snapshots.find_one({"project_id": project_id, "idempotency_key": idempotency_key})
        if existing:
            return envelope(existing)
    metrics = (await coverage(project_id, build=str(payload.get("build") or ""), release=str(payload.get("release") or ""), user=user))["data"]
    snapshot = {
        "_id": new_id("COV"),
        "project_id": project_id,
        "label": str(payload.get("label") or ""),
        "idempotency_key": idempotency_key,
        "metrics": metrics,
        "created_by": user.id,
        "created_at": now(),
    }
    try:
        await database.value.coverage_snapshots.insert_one(snapshot)
    except Exception:
        if idempotency_key:
            existing = await database.value.coverage_snapshots.find_one({"project_id": project_id, "idempotency_key": idempotency_key})
            if existing:
                return envelope(existing)
        raise
    await audit(user.id, "coverage_snapshot_created", "CoverageSnapshot", snapshot["_id"], project_id)
    return envelope(snapshot)


@router.get("/test-cases/{test_case_id}/trace")
async def test_case_trace(test_case_id: str, user: CurrentUser = Depends(get_current_user)):
    test_case = await get_project_entity("test_cases", test_case_id, user, "trace.read")
    links = await database.value.trace_links.find({"project_id": test_case["project_id"], "target_type": "test_case_version", "target_id": {"$in": [test_case.get("current_version_id")]}}).to_list(5000)
    return envelope({"test_case": test_case, "trace_links": links})


@router.get("/projects/{project_id}/traceability/export")
async def export_traceability(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "report.export")
    links = await database.value.trace_links.find({"project_id": project_id}).to_list(50000)
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["source_type", "source_id", "target_type", "target_id", "link_type", "status", "confidence", "origin"])
    writer.writeheader()
    for link in links:
        writer.writerow({key: link.get(key) for key in writer.fieldnames})
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="traceability-{project_id}.csv"'})


async def validate_artifact(artifact_type, artifact_id, project_id):
    mapping = {
        "requirement_version": "requirement_versions",
        "acceptance_criterion": "acceptance_criteria",
        "test_scenario": "test_scenarios",
        "test_case_version": "test_case_versions",
    }
    collection = mapping[artifact_type]
    if not await database.value[collection].find_one({"_id": artifact_id, "project_id": project_id}):
        raise HTTPException(status_code=422, detail={"code": "CROSS_PROJECT_OR_MISSING_ARTIFACT"})


def percent(value, total):
    return round(value * 100 / total, 2) if total else 0
