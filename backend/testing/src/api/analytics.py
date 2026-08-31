import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope, get_project, now
from src.core.database import database
from src.core.configuration import settings
from src.domain.schemas import ProjectQuestionInput, SearchInput
from src.services.project_knowledge import search_project_with_status


router = APIRouter(prefix="/api/qa", tags=["QA Analytics"])


@router.get("/projects/{project_id}/dashboard")
async def dashboard(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "analytics.read")
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
    project = await get_project(project_id, user, "knowledge.read")
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
        ("requirement_document", "requirement_documents", "normalized_content"),
    ]
    for artifact_type, collection, text_field in sources:
        if requested and artifact_type not in requested:
            continue
        source_query = {
            "project_id": project_id,
            "$or": [
                {text_field: {"$regex": pattern, "$options": "i"}},
                {"title": {"$regex": pattern, "$options": "i"}},
            ],
        }
        if artifact_type == "requirement_document":
            source_query["status"] = {"$ne": "ARCHIVED"}
        documents = await database.value[collection].find(source_query).limit(payload.limit).to_list(payload.limit)
        for item in documents:
            authority = item.get("authority") or (
                "baseline" if item.get("status") == "BASELINED" else "draft"
            )
            results.append({"artifact_type": artifact_type, "artifact_id": item.get("requirement_id") or item.get("test_case_id") or item["_id"], "artifact_version_id": item["_id"], "title": item.get("title") or item.get("name") or item.get("filename"), "text": str(item.get(text_field, ""))[:1000], "status": item.get("status"), "authority": authority, "source_type": item.get("source_type"), "teacher_id": item.get("teacher_id"), "subject": item.get("subject"), "grade": item.get("grade"), "project_id": project_id, "score": lexical_score(payload.query, str(item.get(text_field, "")) + " " + str(item.get("title", "")) + " " + str(item.get("filename", "")))})
    by_version = {item.get("artifact_version_id"): item for item in results}
    for item in dense:
        version_id = item.get("artifact_version_id")
        if version_id in by_version:
            by_version[version_id]["score"] = round(0.45 * by_version[version_id]["score"] + 0.55 * item["score"], 4)
            by_version[version_id]["retrieval_source"] = "hybrid_fusion"
        else:
            by_version[version_id] = item
    results = list(by_version.values())
    authority_order = (project.get("settings") or {}).get(
        "knowledge_authority_order",
        ["teacher", "official", "baseline", "supplemental", "reference", "draft"],
    )
    authority_rank = {value: index for index, value in enumerate(authority_order)}
    results.sort(
        key=lambda item: (
            authority_rank.get(item.get("authority"), len(authority_rank)),
            -item.get("score", 0),
        )
    )
    return envelope({"items": results[: payload.limit], "filters": {"project_id": project_id, "artifact_types": list(requested)}, "retrieval_version": "project-hybrid-knowledge-v1", "degraded_mode": dense_result["degraded_mode"], "fallback": dense_result["degraded_mode"] != "NORMAL", "error_code": dense_result["error_code"]}, degraded_mode=dense_result["degraded_mode"] if dense_result["degraded_mode"] != "NORMAL" else None)


@router.post("/projects/{project_id}/ai/ask")
async def ask_project(
    project_id: str,
    payload: ProjectQuestionInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "ai.ask_project")
    await get_project(project_id, user, "knowledge.read")
    search_result = await search_knowledge(project_id, SearchInput(query=payload.question, artifact_types=payload.artifact_types, limit=payload.evidence_limit), user)
    evidence = search_result["data"]["items"]
    if not evidence:
        return envelope({"answer": "Không có đủ bằng chứng trong dự án để trả lời câu hỏi này", "evidence": [], "confidence": 0, "warnings": ["PROJECT_EVIDENCE_NOT_FOUND"], "model": {"provider": "none", "retrieval_version": search_result["data"]["retrieval_version"]}})
    request = {
        "capability": "project_question",
        "project_id": project_id,
        "instruction": payload.question,
        "evidence": evidence,
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{settings.AI_URL.rstrip('/')}/suy-luan/noi-bo/qa/ho-tro", headers={"X-Internal-Token": settings.SECRET_KEY}, json=request)
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail={"code": "AI_PROVIDER_UNAVAILABLE", "retryable": True}) from error
    await database.value.ai_request_audit.insert_one({"_id": f"ASK-{search_result['meta']['trace_id']}", "project_id": project_id, "capability": "project_question", "requested_by": user.id, "evidence_refs": result.get("evidence_refs", []), "model": result.get("model", {}), "status": result.get("status"), "created_at": now()})
    return envelope({"answer": result.get("answer") or "Không có câu trả lời có căn cứ", "evidence": evidence, "confidence": result.get("confidence", 0), "warnings": result.get("warnings", []), "model": result.get("model", {}), "reason_codes": result.get("reason_codes", [])}, status=result.get("status", "SUCCESS"), degraded_mode=result.get("degraded_mode"))


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
    await get_project(project_id, user, "analytics.read")
    impact_count = await database.value.impact_analyses.count_documents({"project_id": project_id})
    stale_count = await database.value.test_cases.count_documents({"project_id": project_id, "status": "NEEDS_UPDATE"})
    return envelope({"impact_analysis_count": impact_count, "tests_stale": stale_count})


@router.get("/projects/{project_id}/ai-analytics")
async def ai_analytics(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "analytics.ai.read")
    pipeline = [
        {"$match": {"project_id": project_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    proposal_status = await database.value.maintenance_proposals.aggregate(pipeline).to_list(100)
    accepted = sum(item["count"] for item in proposal_status if item["_id"] in {"ACCEPTED", "EDITED_ACCEPTED"})
    reviewed = sum(item["count"] for item in proposal_status if item["_id"] != "PENDING")
    impact_rows = await database.value.impact_analyses.find(
        {"project_id": project_id},
        {"ai_result": 1, "review_overrides": 1, "model_version": 1},
    ).to_list(10000)
    measured = [item for item in impact_rows if isinstance(item.get("ai_result"), dict)]
    degraded = sum(
        1
        for item in measured
        if item["ai_result"].get("status") != "SUCCESS"
        or item["ai_result"].get("degraded_mode")
    )
    latencies = [
        item["ai_result"].get("latency_ms")
        for item in measured
        if isinstance(item["ai_result"].get("latency_ms"), (int, float))
    ]
    model_versions = {}
    for item in impact_rows:
        ai_result = item.get("ai_result") or {}
        model = ai_result.get("model") if isinstance(ai_result.get("model"), dict) else {}
        model_version = item.get("model_version") or model.get("version") or "unknown"
        model_versions[model_version] = model_versions.get(model_version, 0) + 1
    return envelope(
        {
            "proposal_status": proposal_status,
            "proposal_acceptance_rate": round(accepted / reviewed, 4) if reviewed else None,
            "override_count": sum(len(item.get("review_overrides") or []) for item in impact_rows),
            "degraded_count": degraded,
            "degraded_rate": round(degraded / len(measured), 4) if measured else 0,
            "average_latency_ms": round(sum(latencies) / len(latencies), 3) if latencies else 0,
            "model_versions": model_versions,
        }
    )


@router.get("/projects/{project_id}/reports/execution")
async def execution_report(
    project_id: str,
    release: str = Query(default="", max_length=200),
    environment: str = Query(default="", max_length=500),
    build: str = Query(default="", max_length=200),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "report.read")
    run_query = {"project_id": project_id}
    if environment:
        run_query["environment"] = environment
    if build:
        run_query["build"] = build
    if release:
        plans = await database.value.test_plans.find(
            {"project_id": project_id, "release": release}, {"_id": 1}
        ).to_list(5000)
        run_query["test_plan_id"] = {"$in": [item["_id"] for item in plans]}
    runs = await database.value.test_runs.find(run_query, {"_id": 1, "status": 1}).to_list(10000)
    run_ids = [item["_id"] for item in runs]
    result_rows = await database.value.test_results.aggregate(
        [
            {"$match": {"project_id": project_id, "test_run_id": {"$in": run_ids}}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
    ).to_list(20)
    run_status_rows = {}
    for item in runs:
        run_status_rows[item.get("status", "UNKNOWN")] = run_status_rows.get(
            item.get("status", "UNKNOWN"), 0
        ) + 1
    result_counts = {item["_id"]: item["count"] for item in result_rows}
    terminal_count = sum(
        result_counts.get(status, 0)
        for status in ("PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE")
    )
    return envelope(
        {
            "run_count": len(runs),
            "run_status_counts": run_status_rows,
            "result_counts": result_counts,
            "terminal_result_count": terminal_count,
            "pass_rate": round(result_counts.get("PASS", 0) / terminal_count, 4)
            if terminal_count
            else None,
            "scope": {"release": release or None, "environment": environment or None, "build": build or None},
        }
    )


@router.get("/projects/{project_id}/reports/defects")
async def defect_report(
    project_id: str,
    release: str = Query(default="", max_length=200),
    environment: str = Query(default="", max_length=500),
    build: str = Query(default="", max_length=200),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "report.read")
    query = {"project_id": project_id}
    if release:
        query["release"] = release
    if environment:
        query["environment"] = environment
    if build:
        query["build"] = build
    defects = await database.value.defects.find(
        query, {"status": 1, "severity": 1, "created_at": 1}
    ).to_list(50000)
    status_counts = {}
    severity_counts = {}
    open_ages = []
    timestamp = now()
    terminal_statuses = {"CLOSED", "REJECTED", "DUPLICATE"}
    for item in defects:
        status_value = item.get("status", "UNKNOWN")
        severity_value = item.get("severity", "unknown")
        status_counts[status_value] = status_counts.get(status_value, 0) + 1
        severity_counts[severity_value] = severity_counts.get(severity_value, 0) + 1
        created_at = item.get("created_at")
        if status_value not in terminal_statuses and created_at:
            open_ages.append(max(0, (timestamp - created_at).total_seconds() / 86400))
    reopened_count = await database.value.defect_retests.count_documents(
        {"project_id": project_id, "outcome": "FAIL", "application_status": "APPLIED"}
    )
    return envelope(
        {
            "defect_count": len(defects),
            "open_count": sum(
                count for status_value, count in status_counts.items() if status_value not in terminal_statuses
            ),
            "status_counts": status_counts,
            "severity_counts": severity_counts,
            "reopened_count": reopened_count,
            "average_open_age_days": round(sum(open_ages) / len(open_ages), 2) if open_ages else 0,
            "scope": {"release": release or None, "environment": environment or None, "build": build or None},
        }
    )


@router.get("/projects/{project_id}/activity")
async def project_activity(
    project_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "analytics.read")
    excluded_actions = {
        "project_member_added",
        "project_member_updated",
        "project_member_removed",
        "project_invitation_created",
        "project_invitation_cancelled",
        "project_invitation_resent",
    }
    events = await database.value.audit_events.find(
        {"project_id": project_id, "action": {"$nin": sorted(excluded_actions)}},
        {"action": 1, "entity_type": 1, "entity_id": 1, "created_at": 1},
    ).sort("created_at", -1).to_list(limit)
    return envelope(events)


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
