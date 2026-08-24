import json
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from pydantic import Field

from src.core.infrastructure.configuration import settings
from src.tools.http_client import INTERNAL_API_URL, make_api_request


def headers(config):
    token = (config or {}).get("configurable", {}).get("token")
    return {"Authorization": token, "X-Internal-Token": settings.SECRET_KEY} if token else None


async def call(method, path, config, payload=None):
    request_headers = headers(config)
    if not request_headers:
        return json.dumps({"status": "authentication_required"})
    response = await make_api_request(method, f"{INTERNAL_API_URL}/api/qa{path}", headers=request_headers, json=payload, timeout=60)
    try:
        body = response.json()
    except ValueError:
        body = {"error": {"code": "UPSTREAM_RESPONSE_INVALID"}}
    if response.status_code >= 400:
        return json.dumps({"status": "qa_operation_failed", "upstream_status": response.status_code, "error": body.get("error")}, ensure_ascii=False)
    return json.dumps(body.get("data", body), ensure_ascii=False, default=str)


def parse(value):
    try:
        result = json.loads(value)
        return result if isinstance(result, dict) else None
    except (TypeError, json.JSONDecodeError):
        return None


@tool
async def get_project_context(project_id: Annotated[str, Field(description="Mã Project QA")], config: RunnableConfig = None) -> str:
    """Lấy Project và dashboard trong đúng tenant hiện tại"""
    project = await call("GET", f"/projects/{project_id}", config)
    dashboard = await call("GET", f"/projects/{project_id}/dashboard", config)
    return json.dumps({"project": json.loads(project), "dashboard": json.loads(dashboard)}, ensure_ascii=False)


@tool
async def search_project_knowledge(project_id: Annotated[str, Field(description="Mã Project QA")], query: Annotated[str, Field(min_length=1, description="Truy vấn artifact")], config: RunnableConfig = None) -> str:
    """Tìm bằng chứng chỉ trong một Project QA"""
    return await call("POST", f"/projects/{project_id}/knowledge/search", config, {"query": query, "artifact_types": [], "limit": 20})


@tool
async def get_requirement_version(requirement_id: Annotated[str, Field(description="Mã Requirement")], config: RunnableConfig = None) -> str:
    """Lấy Requirement cùng phiên bản hiện tại và Acceptance Criteria"""
    return await call("GET", f"/requirements/{requirement_id}", config)


@tool
async def compare_requirement_versions(requirement_id: Annotated[str, Field(description="Mã Requirement")], from_version_id: Annotated[str, Field(description="Phiên bản nguồn")], to_version_id: Annotated[str, Field(description="Phiên bản đích")], config: RunnableConfig = None) -> str:
    """So sánh ngữ nghĩa hai phiên bản của cùng Requirement"""
    return await call("POST", f"/requirements/{requirement_id}/compare", config, {"from_version_id": from_version_id, "to_version_id": to_version_id})


@tool
async def get_acceptance_criteria(requirement_id: Annotated[str, Field(description="Mã Requirement")], config: RunnableConfig = None) -> str:
    """Lấy Acceptance Criteria có version và authority"""
    return await call("GET", f"/requirements/{requirement_id}", config)


@tool
async def get_trace_links(project_id: Annotated[str, Field(description="Mã Project QA")], config: RunnableConfig = None) -> str:
    """Lấy ma trận Trace Link gồm trạng thái xác nhận"""
    return await call("GET", f"/projects/{project_id}/traceability", config)


@tool
async def search_test_cases(project_id: Annotated[str, Field(description="Mã Project QA")], query: Annotated[str, Field(description="Từ khóa Test Case")] = "", config: RunnableConfig = None) -> str:
    """Tìm Test Case trong đúng Project QA"""
    return await call("GET", f"/projects/{project_id}/test-cases?q={query}", config)


@tool
async def get_test_case_version(test_case_id: Annotated[str, Field(description="Mã Test Case")], config: RunnableConfig = None) -> str:
    """Lấy toàn bộ lịch sử Test Case Version bất biến"""
    return await call("GET", f"/test-cases/{test_case_id}/versions", config)


@tool
async def get_test_results(test_run_id: Annotated[str, Field(description="Mã Test Run")], config: RunnableConfig = None) -> str:
    """Lấy snapshot Test Run kết quả và Defect liên quan"""
    return await call("GET", f"/test-runs/{test_run_id}", config)


@tool
async def get_historical_defects(project_id: Annotated[str, Field(description="Mã Project QA")], config: RunnableConfig = None) -> str:
    """Lấy lịch sử Defect để làm evidence cho đề xuất kiểm thử"""
    return await call("GET", f"/projects/{project_id}/defects", config)


@tool
async def find_near_duplicates(project_id: Annotated[str, Field(description="Mã Project QA")], config: RunnableConfig = None) -> str:
    """Tìm các Test Case gần trùng và trả bằng chứng cấu trúc"""
    return await call("GET", f"/projects/{project_id}/test-cases/duplicates", config)


@tool
async def create_test_case_draft(project_id: Annotated[str, Field(description="Mã Project QA")], draft_json: Annotated[str, Field(description="TestCaseDraft JSON có Tiptap JSON")], config: RunnableConfig = None) -> str:
    """Tạo Test Case Draft để con người rà soát"""
    payload = parse(draft_json)
    return await call("POST", f"/projects/{project_id}/test-case-drafts", config, payload) if payload else json.dumps({"status": "invalid_payload"})


@tool
async def create_trace_link_suggestion(trace_json: Annotated[str, Field(description="TraceLink JSON với evidence confidence và project_id")], config: RunnableConfig = None) -> str:
    """Tạo Trace Link suggestion không tự xác nhận"""
    payload = parse(trace_json)
    if payload:
        payload["origin"] = "ai_suggested"
    return await call("POST", "/trace-links", config, payload) if payload else json.dumps({"status": "invalid_payload"})


@tool
async def create_impact_analysis(change_set_id: Annotated[str, Field(description="Mã Change Set")], config: RunnableConfig = None) -> str:
    """Chạy impact analysis có evidence trên Change Set"""
    return await call("POST", f"/change-sets/{change_set_id}/impact-analysis", config)


@tool
async def create_maintenance_proposal(impact_analysis_id: Annotated[str, Field(description="Mã Impact Analysis")], config: RunnableConfig = None) -> str:
    """Tạo proposal bảo trì ở trạng thái chờ con người duyệt"""
    return await call("POST", f"/impact-analyses/{impact_analysis_id}/maintenance-proposals", config)


@tool
async def create_regression_recommendation(change_set_id: Annotated[str, Field(description="Mã Change Set")], config: RunnableConfig = None) -> str:
    """Tạo khuyến nghị regression dựa trên rủi ro trace và lịch sử lỗi"""
    return await call("POST", f"/change-sets/{change_set_id}/regression-recommendation", config)


@tool
async def confirm_trace_link(trace_link_id: Annotated[str, Field(description="Mã Trace Link")], config: RunnableConfig = None) -> str:
    """Xác nhận Trace Link sau quyết định rõ ràng của con người"""
    return await call("POST", f"/trace-links/{trace_link_id}/confirm", config)


@tool
async def baseline_requirement_version(requirement_version_id: Annotated[str, Field(description="Mã Requirement Version")], expected_revision: Annotated[int, Field(ge=1, description="Revision hiện tại")], config: RunnableConfig = None) -> str:
    """Baseline Requirement Version sau phê duyệt rõ ràng của con người"""
    return await call("POST", f"/requirement-versions/{requirement_version_id}/baseline", config, {"expected_revision": expected_revision})


@tool
async def approve_test_case_version(test_case_draft_id: Annotated[str, Field(description="Mã Test Case Draft")], expected_revision: Annotated[int, Field(ge=1, description="Revision hiện tại")], change_reason: Annotated[str, Field(description="Lý do phê duyệt")], config: RunnableConfig = None) -> str:
    """Đóng băng Test Case Draft thành version sau phê duyệt của con người"""
    return await call("POST", f"/test-case-drafts/{test_case_draft_id}/freeze", config, {"expected_revision": expected_revision, "change_reason": change_reason})


@tool
async def mark_test_case_obsolete(test_case_id: Annotated[str, Field(description="Mã Test Case")], expected_current_version_id: Annotated[str, Field(description="Phiên bản hiện tại")], reason: Annotated[str, Field(min_length=2, description="Lý do obsolete đã được người dùng xác nhận")], config: RunnableConfig = None) -> str:
    """Đánh dấu Test Case obsolete sau quyết định rõ ràng của con người"""
    return await call("POST", f"/test-cases/{test_case_id}/obsolete", config, {"expected_current_version_id": expected_current_version_id, "reason": reason})


@tool
async def apply_test_case_revision(proposal_id: Annotated[str, Field(description="Mã Maintenance Proposal")], expected_revision: Annotated[int, Field(ge=1, description="Revision của proposal")], patch_json: Annotated[str, Field(description="JSON chỉnh sửa đã được người dùng duyệt")] = "{}", config: RunnableConfig = None) -> str:
    """Áp dụng Test Case revision qua proposal đã được con người chấp nhận"""
    patch = parse(patch_json)
    return await call("POST", f"/maintenance-proposals/{proposal_id}/accept-with-edit", config, {"expected_revision": expected_revision, "patch": patch or {}, "review_note": "Approved through QA agent tool"})
