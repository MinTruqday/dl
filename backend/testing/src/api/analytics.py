import re

from fastapi import APIRouter, Depends, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope, get_project
from src.core.database import database
from src.domain.schemas import SearchInput
from src.services.project_knowledge import search_project_with_status


router = APIRouter(prefix="/api/qa", tags=["QA Analytics"])


@router.get("/projects/{project_id}/dashboard")
async def dashboard(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "coverage.read")
    requirements = await database.value.requirements.count_documents({"project_id": project_id, "status": "BASELINED"})
    active_tests = await database.value.test_cases.count_documents({"project_id": project_id, "status": "ACTIVE"})
    stale_tests = await database.value.test_cases.count_documents({"project_id": project_id, "status": "NEEDS_UPDATE"})
    pending_proposals = await database.value.maintenance_proposals.count_documents({"project_id": project_id, "status": "PENDING"})
    current_runs = await database.value.test_runs.count_documents({"project_id": project_id, "status": {"$in": ["READY", "IN_PROGRESS"]}})
    open_defects = await database.value.defects.count_documents({"project_id": project_id, "status": {"$nin": ["CLOSED", "REJECTED", "DUPLICATE"]}})
    defect_severity_rows = await database.value.defects.aggregate(
        [
            {
                "$match": {
                    "project_id": project_id,
                    "status": {"$nin": ["CLOSED", "REJECTED", "DUPLICATE"]},
                }
            },
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
        ]
    ).to_list(20)
    open_defects_by_severity = {
        severity: next(
            (item["count"] for item in defect_severity_rows if item["_id"] == severity),
            0,
        )
        for severity in ("blocker", "critical", "major", "minor", "trivial")
    }
    latest_run = await database.value.test_runs.find_one(
        {"project_id": project_id}, sort=[("updated_at", -1)]
    )
    latest_run_summary = None
    if latest_run:
        result_rows = await database.value.test_results.aggregate(
            [
                {"$match": {"project_id": project_id, "test_run_id": latest_run["_id"]}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            ]
        ).to_list(20)
        latest_run_summary = {
            "_id": latest_run["_id"],
            "name": latest_run["name"],
            "status": latest_run["status"],
            "environment": latest_run.get("environment"),
            "build": latest_run.get("build"),
            "result_counts": {item["_id"]: item["count"] for item in result_rows},
            "updated_at": latest_run.get("updated_at"),
        }
    changes_waiting_impact = await database.value.requirement_change_sets.count_documents(
        {"project_id": project_id, "status": {"$in": ["READY", "REVIEWED"]}}
    )
    changes_waiting_impact += await database.value.impact_analyses.count_documents(
        {"project_id": project_id, "status": "REVIEW_READY"}
    )
    coverage = await coverage_snapshot(project_id)
    recent_changes = await database.value.requirement_change_sets.find({"project_id": project_id}).sort("created_at", -1).to_list(10)
    return envelope({"requirements": requirements, "active_tests": active_tests, "tests_needing_update": stale_tests, "pending_proposals": pending_proposals, "current_runs": current_runs, "open_defects": open_defects, "open_defects_by_severity": open_defects_by_severity, "latest_run": latest_run_summary, "changes_waiting_impact": changes_waiting_impact, **coverage, "recent_changes": recent_changes})


@router.post("/projects/{project_id}/knowledge/search")
async def search_knowledge(
    project_id: str,
    payload: SearchInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "knowledge.read")
    dense_result = await search_project_with_status(project_id, payload.query, payload.artifact_types, payload.limit)
    dense = dense_result["items"]
    pattern = re.escape(payload.query)
    requested = set(payload.artifact_types)
    results = []
    sources = [
        ("requirement_version", "requirement_versions", "plain_text_projection"),
        ("test_case_version", "test_case_versions", "plain_text_projection"),
        ("defect", "defects", "title"),
        ("test_plan", "test_plans", "objective"),
    ]
    for artifact_type, collection, text_field in sources:
        if requested and artifact_type not in requested:
            continue
        documents = await database.value[collection].find({"project_id": project_id, "$or": [{text_field: {"$regex": pattern, "$options": "i"}}, {"title": {"$regex": pattern, "$options": "i"}}]}).limit(payload.limit).to_list(payload.limit)
        for item in documents:
            authority = "baseline" if item.get("status") == "BASELINED" else "draft"
            results.append({"artifact_type": artifact_type, "artifact_id": item.get("requirement_id") or item.get("test_case_id") or item["_id"], "artifact_version_id": item["_id"], "title": item.get("title") or item.get("name"), "text": str(item.get(text_field, ""))[:1000], "status": item.get("status"), "authority": authority, "project_id": project_id, "score": lexical_score(payload.query, str(item.get(text_field, "")) + " " + str(item.get("title", "")))})
    by_version = {item.get("artifact_version_id"): item for item in results}
    for item in dense:
        version_id = item.get("artifact_version_id")
        if version_id in by_version:
            by_version[version_id]["score"] = round(0.45 * by_version[version_id]["score"] + 0.55 * item["score"], 4)
            by_version[version_id]["retrieval_source"] = "hybrid_fusion"
        else:
            by_version[version_id] = item
    results = list(by_version.values())
    results.sort(key=lambda item: (item.get("authority") != "baseline", -item.get("score", 0)))
    return envelope({"items": results[: payload.limit], "filters": {"project_id": project_id, "artifact_types": list(requested)}, "retrieval_version": "project-hybrid-knowledge-v1", "degraded_mode": dense_result["degraded_mode"], "fallback": dense_result["degraded_mode"] != "NORMAL", "error_code": dense_result["error_code"]}, degraded_mode=dense_result["degraded_mode"] if dense_result["degraded_mode"] != "NORMAL" else None)


@router.get("/projects/{project_id}/audit")
async def project_audit(
    project_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "project.audit.read")
    return envelope(await database.value.audit_events.find({"project_id": project_id}).sort("created_at", -1).to_list(limit))


@router.get("/projects/{project_id}/maintenance-analytics")
async def maintenance_analytics(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "coverage.read")
    pipeline = [
        {"$match": {"project_id": project_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    proposal_status = await database.value.maintenance_proposals.aggregate(pipeline).to_list(100)
    impact_count = await database.value.impact_analyses.count_documents({"project_id": project_id})
    stale_count = await database.value.test_cases.count_documents({"project_id": project_id, "status": "NEEDS_UPDATE"})
    accepted = sum(item["count"] for item in proposal_status if item["_id"] in {"ACCEPTED", "EDITED_ACCEPTED"})
    reviewed = sum(item["count"] for item in proposal_status if item["_id"] != "PENDING")
    return envelope({"proposal_status": proposal_status, "proposal_acceptance_rate": round(accepted / reviewed, 4) if reviewed else None, "impact_analysis_count": impact_count, "tests_stale": stale_count})


async def coverage_snapshot(project_id):
    requirements = await database.value.requirements.find({"project_id": project_id, "status": "BASELINED"}).to_list(10000)
    requirement_versions = {item["current_version_id"] for item in requirements}
    criteria = await database.value.acceptance_criteria.find({"project_id": project_id, "requirement_version_id": {"$in": list(requirement_versions)}, "status": {"$ne": "obsolete"}}).to_list(20000)
    links = await database.value.trace_links.find({"project_id": project_id, "status": "CONFIRMED"}).to_list(50000)
    covered_requirements = {item["source_id"] for item in links if item["source_type"] == "requirement_version"}
    covered_criteria = {item["source_id"] for item in links if item["source_type"] == "acceptance_criterion"}
    return {"requirement_coverage": percentage(len(requirement_versions & covered_requirements), len(requirement_versions)), "acceptance_criterion_coverage": percentage(len({item["_id"] for item in criteria} & covered_criteria), len(criteria)), "unlinked_tests": await database.value.test_cases.count_documents({"project_id": project_id, "current_version_id": {"$nin": [item["target_id"] for item in links]}})}


def percentage(value, total):
    return round(value * 100 / total, 2) if total else 0


def lexical_score(query, text):
    terms = set(re.findall(r"\w+", query.lower()))
    words = set(re.findall(r"\w+", text.lower()))
    return round(len(terms & words) / max(1, len(terms)), 4)
