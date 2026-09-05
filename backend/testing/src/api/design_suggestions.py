from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, new_id, now
from src.core.database import database
from src.domain.schemas import PerformancePlanDraftInput, SecurityTestSuggestionInput
from src.services.design_assistance import request_design_assistance


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


def security_candidates(categories, versions):
    definitions = {
        "authorization": (
            "Từ chối thao tác vượt quyền",
            "Thực hiện thao tác được bảo vệ bằng vai trò không đủ quyền",
            "Hệ thống từ chối yêu cầu và không thay đổi dữ liệu",
        ),
        "authentication": (
            "Từ chối danh tính không hợp lệ",
            "Gửi thông tin xác thực sai hoặc đã bị thu hồi",
            "Hệ thống từ chối xác thực và ghi nhận sự kiện an toàn",
        ),
        "input_validation": (
            "Kiểm tra dữ liệu đầu vào không hợp lệ",
            "Gửi dữ liệu sai kiểu vượt biên và chứa chuỗi điều khiển",
            "Hệ thống từ chối an toàn không thực thi nội dung và không rò rỉ chi tiết nội bộ",
        ),
        "session": (
            "Từ chối phiên hết hạn hoặc bị thu hồi",
            "Dùng lại phiên đã hết hạn hoặc đã đăng xuất",
            "Hệ thống từ chối phiên và yêu cầu xác thực lại",
        ),
        "data_protection": (
            "Không lộ dữ liệu nhạy cảm",
            "Quan sát phản hồi nhật ký và tệp xuất trong luồng nghiệp vụ",
            "Dữ liệu nhạy cảm được che giấu và chỉ hiển thị theo quyền",
        ),
    }
    refs = [item["_id"] for item in versions]
    return [
        {
            "candidate_id": f"SEC-{index}",
            "category": category,
            "title": definitions[category][0],
            "preconditions": ["Dùng môi trường kiểm thử được cô lập"],
            "action": definitions[category][1],
            "expected": definitions[category][2],
            "requirement_version_ids": refs,
            "origin": "ai_assisted_draft",
            "status": "SUGGESTED",
        }
        for index, category in enumerate(categories, 1)
    ]


def performance_scenarios(payload):
    factors = {
        "baseline": 0.25,
        "load": 1,
        "stress": 1.5,
        "spike": 2,
        "soak": 0.75,
    }
    return [
        {
            "scenario_id": f"PERF-{index}",
            "workload_type": workload,
            "virtual_users": max(1, round(payload.target_virtual_users * factors[workload])),
            "requests_per_second": (
                round(payload.target_requests_per_second * factors[workload], 2)
                if payload.target_requests_per_second
                else None
            ),
            "duration_minutes": (
                max(payload.duration_minutes, 240)
                if workload == "soak"
                else payload.duration_minutes
            ),
            "ramp_pattern": "immediate" if workload == "spike" else "gradual",
        }
        for index, workload in enumerate(payload.workload_types, 1)
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
        "Tạo đề xuất kiểm thử authorization authentication input session data protection chỉ từ evidence và không tuyên bố đã quét lỗ hổng",
        evidence
        + ([{"artifact_type": "user_context", "text": payload.context}] if payload.context else []),
    )
    timestamp = now()
    result = {
        "_id": new_id("SECSUG"),
        "project_id": project_id,
        "result_type": "SECURITY_TEST_SUGGESTION",
        "categories": payload.categories,
        "requirement_version_ids": [item["_id"] for item in versions],
        "candidates": security_candidates(payload.categories, versions),
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
        "Tạo bản nháp workload scenario metric threshold chỉ từ evidence và không chạy công cụ phát tải",
        evidence
        + ([{"artifact_type": "user_context", "text": payload.context}] if payload.context else []),
    )
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
        "scenarios": performance_scenarios(payload),
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
