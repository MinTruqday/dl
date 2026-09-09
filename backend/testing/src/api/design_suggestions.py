import json

from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, new_id, now
from src.core.database import database
from src.domain.schemas import PerformancePlanDraftInput, SecurityTestSuggestionInput
from src.services.design_assistance import request_design_assistance
from src.services.generation import SecurityCandidate, PerformanceScenario, validated_suggestions


router = APIRouter(prefix="/kiem-thu", tags=["Thiết kế kiểm thử chuyên sâu"])


async def requirement_evidence(project_id, requirement_version_ids):
    query = {"project_id": project_id}
    if requirement_version_ids:
        query["_id"] = {"$in": list(dict.fromkeys(requirement_version_ids))}
    versions = await database.value.requirement_versions.find(query).sort(
        "created_at", -1
    ).to_list(500)
    if requirement_version_ids and len(versions) != len(set(requirement_version_ids)):
        raise HTTPException(status_code=422, detail={"code": "INVALID_REQUIREMENT_VERSION"})
    return versions, [
        {
            "artifact_type": "requirement_version",
            "artifact_id": item.get("requirement_id"),
            "artifact_version_id": item["_id"],
            "authority": "PROJECT_BASELINE",
            "text": " ".join(
                filter(
                    None,
                    [
                        str(item.get("title") or ""),
                        str(item.get("plain_text_projection") or ""),
                    ],
                )
            )[:4000],
        }
        for item in versions
    ]


@router.get("/du-an/{project_id}/ai/goi-y-kiem-thu-bao-mat")
async def list_security_test_suggestions(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "ai.generate_security_tests")
    items = await database.value.security_test_suggestions.find(
        {"project_id": project_id}
    ).sort("created_at", -1).to_list(200)
    return envelope(items)


@router.post(
    "/du-an/{project_id}/ai/goi-y-kiem-thu-bao-mat",
    status_code=201,
)
async def generate_security_test_suggestions(
    project_id: str,
    payload: SecurityTestSuggestionInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "ai.generate_security_tests")
    existing = await database.value.security_test_suggestions.find_one(
        {"project_id": project_id, "idempotency_key": payload.idempotency_key}
    )
    if existing:
        return envelope(existing, revision=existing["revision"])
    versions, evidence = await requirement_evidence(
        project_id, payload.requirement_version_ids
    )
    ai_result = await request_design_assistance(
        "security_test_generation",
        project_id,
        json.dumps({"task": "Sinh kiểm thử bảo mật cụ thể theo bằng chứng bằng tiếng Việt không tuyên bố đã quét lỗ hổng mỗi nhóm có ít nhất một đề xuất", "categories": payload.categories, "suggestion_schema": SecurityCandidate.model_json_schema()}, ensure_ascii=False),
        evidence
        + [
            {
                "artifact_type": "design_request",
                "artifact_id": payload.idempotency_key,
                "authority": "USER_REQUEST",
                "text": json.dumps(
                    {"categories": payload.categories, "context": payload.context},
                    ensure_ascii=False,
                ),
            }
        ],
    )
    candidates = validated_suggestions(ai_result, SecurityCandidate)
    version_ids = {item["_id"] for item in versions}
    if {item["category"] for item in candidates} != set(payload.categories) or any(not set(item["requirement_version_ids"]) <= version_ids for item in candidates):
        raise HTTPException(502, detail={"code": "AI_GENERATION_INVALID"})
    candidates = [{**item, "candidate_id": f"SEC-{index}", "status": "SUGGESTED", "origin": "ai_generated"} for index, item in enumerate(candidates, 1)]
    timestamp = now()
    result = {
        "_id": new_id("SECSUG"),
        "project_id": project_id,
        "result_type": "SECURITY_TEST_SUGGESTION",
        "categories": payload.categories,
        "requirement_version_ids": [item["_id"] for item in versions],
        "candidates": candidates,
        "model_suggestions": ai_result.get("suggestions", []),
        "evidence_refs": ai_result.get("evidence_refs", []),
        "confidence": ai_result.get("confidence", 0),
        "warnings": ai_result.get("warnings", []),
        "model": ai_result.get("model", {}),
        "latency_ms": ai_result.get("latency_ms"),
        "status": "PENDING_REVIEW",
        "generation_status": ai_result.get("status", "SUCCESS"),
        "degraded_mode": ai_result.get("degraded_mode"),
        "candidate_only": True,
        "vulnerability_scan_performed": False,
        "human_confirmation_required": True,
        "idempotency_key": payload.idempotency_key,
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.security_test_suggestions.insert_one(result)
    except DuplicateKeyError:
        existing = await database.value.security_test_suggestions.find_one(
            {"project_id": project_id, "idempotency_key": payload.idempotency_key}
        )
        if existing:
            return envelope(existing, revision=existing["revision"])
        raise
    await audit(
        user.id,
        "security_test_suggestions_generated",
        "SecurityTestSuggestion",
        result["_id"],
        project_id,
        {"candidate_count": len(result["candidates"])},
    )
    return envelope(
        result,
        revision=1,
        status=ai_result.get("status", "SUCCESS"),
        degraded_mode=ai_result.get("degraded_mode"),
    )


@router.get("/du-an/{project_id}/ai/ke-hoach-hieu-nang")
async def list_performance_plan_drafts(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "ai.generate_performance_plan")
    items = await database.value.performance_plan_drafts.find(
        {"project_id": project_id}
    ).sort("created_at", -1).to_list(200)
    return envelope(items)


@router.post("/du-an/{project_id}/ai/ke-hoach-hieu-nang", status_code=201)
async def generate_performance_plan_draft(
    project_id: str,
    payload: PerformancePlanDraftInput,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "ai.generate_performance_plan")
    existing = await database.value.performance_plan_drafts.find_one(
        {"project_id": project_id, "idempotency_key": payload.idempotency_key}
    )
    if existing:
        return envelope(existing, revision=existing["revision"])
    versions, evidence = await requirement_evidence(
        project_id, payload.requirement_version_ids
    )
    ai_result = await request_design_assistance(
        "performance_plan_generation",
        project_id,
        json.dumps({"task": "Sinh kế hoạch hiệu năng bằng tiếng Việt gắn với hành vi trong bằng chứng mỗi workload có ít nhất một kịch bản không chạy phát tải", "workload_types": payload.workload_types, "target_virtual_users": payload.target_virtual_users, "target_requests_per_second": payload.target_requests_per_second, "duration_minutes": payload.duration_minutes, "objective": payload.objective, "suggestion_schema": PerformanceScenario.model_json_schema()}, ensure_ascii=False),
        evidence
        + [
            {
                "artifact_type": "design_request",
                "artifact_id": payload.idempotency_key,
                "authority": "USER_REQUEST",
                "text": json.dumps(
                    {
                        "objective": payload.objective,
                        "workload_types": payload.workload_types,
                        "target_virtual_users": payload.target_virtual_users,
                        "target_requests_per_second": payload.target_requests_per_second,
                        "duration_minutes": payload.duration_minutes,
                        "context": payload.context,
                    },
                    ensure_ascii=False,
                ),
            }
        ],
    )
    scenarios = validated_suggestions(ai_result, PerformanceScenario)
    if {item["workload_type"] for item in scenarios} != set(payload.workload_types):
        raise HTTPException(502, detail={"code": "AI_GENERATION_INVALID"})
    scenarios = [{**item, "scenario_id": f"PERF-{index}"} for index, item in enumerate(scenarios, 1)]
    timestamp = now()
    result = {
        "_id": new_id("PERFPLAN"),
        "project_id": project_id,
        "name": payload.name,
        "objective": payload.objective,
        "requirement_version_ids": [item["_id"] for item in versions],
        "workload": {
            "target_virtual_users": payload.target_virtual_users,
            "target_requests_per_second": payload.target_requests_per_second,
            "duration_minutes": payload.duration_minutes,
        },
        "scenarios": scenarios,
        "metrics": [
            {"key": "response_time_p95_ms", "threshold": payload.response_time_p95_ms},
            {"key": "error_rate", "threshold": payload.maximum_error_rate},
            {"key": "throughput", "threshold": payload.target_requests_per_second},
        ],
        "model_suggestions": ai_result.get("suggestions", []),
        "evidence_refs": ai_result.get("evidence_refs", []),
        "confidence": ai_result.get("confidence", 0),
        "warnings": ai_result.get("warnings", []),
        "model": ai_result.get("model", {}),
        "latency_ms": ai_result.get("latency_ms"),
        "status": "DRAFT",
        "generation_status": ai_result.get("status", "SUCCESS"),
        "degraded_mode": ai_result.get("degraded_mode"),
        "load_execution_performed": False,
        "human_confirmation_required": True,
        "idempotency_key": payload.idempotency_key,
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.performance_plan_drafts.insert_one(result)
    except DuplicateKeyError:
        existing = await database.value.performance_plan_drafts.find_one(
            {"project_id": project_id, "idempotency_key": payload.idempotency_key}
        )
        if existing:
            return envelope(existing, revision=existing["revision"])
        raise
    await audit(
        user.id,
        "performance_plan_draft_generated",
        "PerformanceTestPlanDraft",
        result["_id"],
        project_id,
        {"scenario_count": len(result["scenarios"])},
    )
    return envelope(
        result,
        revision=1,
        status=ai_result.get("status", "SUCCESS"),
        degraded_mode=ai_result.get("degraded_mode"),
    )
