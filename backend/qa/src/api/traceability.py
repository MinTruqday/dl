import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.database import database
from src.core.metrics import STALE, TRACE_ACCEPTANCE_RATE, UNCOVERED
from src.domain.schemas import TraceLinkCreate


router = APIRouter(prefix="/api/qa", tags=["QA Traceability"])


@router.post("/trace-links", status_code=201)
async def create_trace_link(
    payload: TraceLinkCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(payload.project_id, user, write=True)
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
        "created_by": user.id,
        "created_at": now(),
        "updated_at": now(),
    }
    await database.value.trace_links.insert_one(link)
    await audit(user.id, "trace_link_created", "TraceLink", link["_id"], payload.project_id)
    return envelope(link)


@router.post("/trace-links/{link_id}/confirm")
async def confirm_trace_link(link_id: str, user: CurrentUser = Depends(get_current_user)):
    return await review_link(link_id, "CONFIRMED", user)


@router.post("/trace-links/{link_id}/reject")
async def reject_trace_link(link_id: str, user: CurrentUser = Depends(get_current_user)):
    return await review_link(link_id, "REJECTED", user)


async def review_link(link_id, status, user):
    link = await get_project_entity("trace_links", link_id, user, write=True)
    await database.value.trace_links.update_one(
        {"_id": link_id},
        {"$set": {"status": status, "reviewed_by": user.id, "reviewed_at": now(), "updated_at": now()}},
    )
    link = await database.value.trace_links.find_one({"_id": link_id})
    reviewed = await database.value.trace_links.count_documents({"project_id": link["project_id"], "status": {"$in": ["CONFIRMED", "REJECTED"]}})
    confirmed = await database.value.trace_links.count_documents({"project_id": link["project_id"], "status": "CONFIRMED"})
    TRACE_ACCEPTANCE_RATE.set(confirmed / reviewed if reviewed else 0)
    await audit(user.id, f"trace_link_{status.lower()}", "TraceLink", link_id, link["project_id"])
    return envelope(link)


@router.get("/projects/{project_id}/traceability")
async def traceability(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user)
    requirements = await database.value.requirements.find({"project_id": project_id}).sort("requirement_key", 1).to_list(5000)
    versions = await database.value.requirement_versions.find({"_id": {"$in": [item["current_version_id"] for item in requirements]}}).to_list(5000)
    criteria = await database.value.acceptance_criteria.find({"project_id": project_id}).to_list(10000)
    tests = await database.value.test_cases.find({"project_id": project_id}).sort("test_case_key", 1).to_list(10000)
    test_versions = await database.value.test_case_versions.find({"_id": {"$in": [item["current_version_id"] for item in tests if item.get("current_version_id")]}}).to_list(10000)
    links = await database.value.trace_links.find({"project_id": project_id}).to_list(50000)
    return envelope({"requirements": requirements, "requirement_versions": versions, "acceptance_criteria": criteria, "test_cases": tests, "test_case_versions": test_versions, "trace_links": links})


@router.get("/projects/{project_id}/coverage")
async def coverage(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user)
    requirements = await database.value.requirements.find({"project_id": project_id, "status": {"$ne": "ARCHIVED"}}).to_list(10000)
    requirement_versions = {item["current_version_id"] for item in requirements}
    criteria = await database.value.acceptance_criteria.find({"project_id": project_id, "status": {"$ne": "obsolete"}}).to_list(20000)
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
    UNCOVERED.set(len(uncovered))
    STALE.set(stale_tests)
    return envelope({"requirement_coverage": requirement_coverage, "acceptance_criterion_coverage": criterion_coverage, "category_coverage": categories, "uncovered_requirements": uncovered, "unlinked_tests": unlinked_tests, "stale_tests": stale_tests})


@router.get("/projects/{project_id}/traceability/export")
async def export_traceability(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user)
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
