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
    response = await make_api_request(method, f"{INTERNAL_API_URL}/kiem-thu{path}", headers=request_headers, json=payload, timeout=60)
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
    project = await call("GET", f"/du-an/{project_id}", config)
    dashboard = await call("GET", f"/du-an/{project_id}/tong-quan", config)
    return json.dumps({"project": json.loads(project), "dashboard": json.loads(dashboard)}, ensure_ascii=False)


@tool
async def search_project_knowledge(project_id: Annotated[str, Field(description="Mã Project QA")], query: Annotated[str, Field(min_length=1, description="Truy vấn artifact")], config: RunnableConfig = None) -> str:
    """Tìm bằng chứng chỉ trong một Project QA"""
    return await call("POST", f"/du-an/{project_id}/tri-thuc/tim-kiem", config, {"query": query, "artifact_types": [], "limit": 20})


@tool
async def get_requirement_version(requirement_id: Annotated[str, Field(description="Mã Requirement")], config: RunnableConfig = None) -> str:
    """Lấy Requirement cùng phiên bản hiện tại và Acceptance Criteria"""
    return await call("GET", f"/yeu-cau/{requirement_id}", config)


@tool
async def compare_requirement_versions(requirement_id: Annotated[str, Field(description="Mã Requirement")], from_version_id: Annotated[str, Field(description="Phiên bản nguồn")], to_version_id: Annotated[str, Field(description="Phiên bản đích")], config: RunnableConfig = None) -> str:
    """So sánh ngữ nghĩa hai phiên bản của cùng Requirement"""
    return await call("POST", f"/yeu-cau/{requirement_id}/so-sanh", config, {"from_version_id": from_version_id, "to_version_id": to_version_id})


@tool
async def get_acceptance_criteria(requirement_id: Annotated[str, Field(description="Mã Requirement")], config: RunnableConfig = None) -> str:
    """Lấy Acceptance Criteria có version và authority"""
    return await call("GET", f"/yeu-cau/{requirement_id}", config)


@tool
async def get_trace_links(project_id: Annotated[str, Field(description="Mã Project QA")], config: RunnableConfig = None) -> str:
    """Lấy ma trận Trace Link gồm trạng thái xác nhận"""
    return await call("GET", f"/du-an/{project_id}/truy-vet", config)


@tool
async def search_test_cases(project_id: Annotated[str, Field(description="Mã Project QA")], query: Annotated[str, Field(description="Từ khóa Test Case")] = "", config: RunnableConfig = None) -> str:
    """Tìm Test Case trong đúng Project QA"""
    return await call("GET", f"/du-an/{project_id}/ca-kiem-thu?q={query}", config)


@tool
async def get_test_case_version(test_case_id: Annotated[str, Field(description="Mã Test Case")], config: RunnableConfig = None) -> str:
    """Lấy toàn bộ lịch sử Test Case Version bất biến"""
    return await call("GET", f"/ca-kiem-thu/{test_case_id}/phien-ban", config)


@tool
async def get_test_results(test_run_id: Annotated[str, Field(description="Mã Test Run")], config: RunnableConfig = None) -> str:
    """Lấy snapshot Test Run kết quả và Defect liên quan"""
    return await call("GET", f"/lan-chay-kiem-thu/{test_run_id}", config)


@tool
async def get_historical_defects(project_id: Annotated[str, Field(description="Mã Project QA")], config: RunnableConfig = None) -> str:
    """Lấy lịch sử Defect để làm evidence cho đề xuất kiểm thử"""
    return await call("GET", f"/du-an/{project_id}/loi", config)


@tool
async def find_near_duplicates(project_id: Annotated[str, Field(description="Mã Project QA")], config: RunnableConfig = None) -> str:
    """Tìm các Test Case gần trùng và trả bằng chứng cấu trúc"""
    return await call("GET", f"/du-an/{project_id}/ca-kiem-thu/trung-lap", config)


@tool
async def create_test_case_draft(project_id: Annotated[str, Field(description="Mã Project QA")], draft_json: Annotated[str, Field(description="TestCaseDraft JSON có Tiptap JSON")], config: RunnableConfig = None) -> str:
    """Tạo Test Case Draft để con người rà soát"""
    payload = parse(draft_json)
    return await call("POST", f"/du-an/{project_id}/ban-nhap-ca-kiem-thu", config, payload) if payload else json.dumps({"status": "invalid_payload"})


@tool
async def create_trace_link_suggestion(trace_json: Annotated[str, Field(description="TraceLink JSON với evidence confidence và project_id")], config: RunnableConfig = None) -> str:
    """Tạo Trace Link suggestion không tự xác nhận"""
    payload = parse(trace_json)
    if payload:
        payload["origin"] = "ai_suggested"
    return await call("POST", "/lien-ket-truy-vet", config, payload) if payload else json.dumps({"status": "invalid_payload"})


@tool
async def create_impact_analysis(change_set_id: Annotated[str, Field(description="Mã Change Set")], config: RunnableConfig = None) -> str:
    """Chạy impact analysis có evidence trên Change Set"""
    return await call("POST", f"/bo-thay-doi/{change_set_id}/phan-tich-anh-huong", config)


@tool
async def create_maintenance_proposal(impact_analysis_id: Annotated[str, Field(description="Mã Impact Analysis")], config: RunnableConfig = None) -> str:
    """Tạo proposal bảo trì ở trạng thái chờ con người duyệt"""
    return await call("POST", f"/phan-tich-anh-huong/{impact_analysis_id}/de-xuat-bao-tri", config)


@tool
async def create_regression_recommendation(change_set_id: Annotated[str, Field(description="Mã Change Set")], config: RunnableConfig = None) -> str:
    """Tạo khuyến nghị regression dựa trên rủi ro trace và lịch sử lỗi"""
    return await call("POST", f"/bo-thay-doi/{change_set_id}/de-xuat-hoi-quy", config)


@tool
async def confirm_trace_link(trace_link_id: Annotated[str, Field(description="Mã Trace Link")], config: RunnableConfig = None) -> str:
    """Xác nhận Trace Link sau quyết định rõ ràng của con người"""
    return await call("POST", f"/lien-ket-truy-vet/{trace_link_id}/xac-nhan", config)


@tool
async def baseline_requirement_version(requirement_version_id: Annotated[str, Field(description="Mã Requirement Version")], expected_revision: Annotated[int, Field(ge=1, description="Revision hiện tại")], config: RunnableConfig = None) -> str:
    """Baseline Requirement Version sau phê duyệt rõ ràng của con người"""
    return await call("POST", f"/phien-ban-yeu-cau/{requirement_version_id}/chot-chuan", config, {"expected_revision": expected_revision})


@tool
async def approve_test_case_version(test_case_draft_id: Annotated[str, Field(description="Mã Test Case Draft")], expected_revision: Annotated[int, Field(ge=1, description="Revision hiện tại")], change_reason: Annotated[str, Field(description="Lý do phê duyệt")], config: RunnableConfig = None) -> str:
    """Đóng băng Test Case Draft thành version sau phê duyệt của con người"""
    return await call("POST", f"/ban-nhap-ca-kiem-thu/{test_case_draft_id}/dong-bang", config, {"expected_revision": expected_revision, "change_reason": change_reason})


@tool
async def mark_test_case_obsolete(test_case_id: Annotated[str, Field(description="Mã Test Case")], expected_current_version_id: Annotated[str, Field(description="Phiên bản hiện tại")], reason: Annotated[str, Field(min_length=2, description="Lý do obsolete đã được người dùng xác nhận")], config: RunnableConfig = None) -> str:
    """Đánh dấu Test Case obsolete sau quyết định rõ ràng của con người"""
    return await call("POST", f"/ca-kiem-thu/{test_case_id}/ngung-hieu-luc", config, {"expected_current_version_id": expected_current_version_id, "reason": reason})


@tool
async def apply_test_case_revision(proposal_id: Annotated[str, Field(description="Mã Maintenance Proposal")], expected_revision: Annotated[int, Field(ge=1, description="Revision của proposal")], patch_json: Annotated[str, Field(description="JSON chỉnh sửa đã được người dùng duyệt")] = "{}", config: RunnableConfig = None) -> str:
    """Áp dụng Test Case revision qua proposal đã được con người chấp nhận"""
    patch = parse(patch_json)
    return await call("POST", f"/de-xuat-bao-tri/{proposal_id}/chap-nhan-co-chinh-sua", config, {"expected_revision": expected_revision, "patch": patch or {}, "review_note": "Approved through QA agent tool"})


@tool
async def retrieve_project_evidence(project_id: Annotated[str, Field(description="Mã Project")], query: Annotated[str, Field(min_length=1, description="Truy vấn bằng chứng")], artifact_types: Annotated[str, Field(description="Danh sách loại artifact phân tách bằng dấu phẩy")] = "", config: RunnableConfig = None) -> str:
    """Truy xuất bằng chứng knowledge trong đúng Project"""
    types = [value.strip() for value in artifact_types.split(",") if value.strip()]
    return await call("POST", f"/du-an/{project_id}/tri-thuc/tim-kiem", config, {"query": query, "artifact_types": types, "limit": 20})


@tool
async def get_requirement(requirement_id: Annotated[str, Field(description="Mã Requirement")], config: RunnableConfig = None) -> str:
    """Lấy Requirement cùng current version"""
    return await call("GET", f"/yeu-cau/{requirement_id}", config)


@tool
async def get_change_facts(change_set_id: Annotated[str, Field(description="Mã Change Set")], config: RunnableConfig = None) -> str:
    """Lấy Change Set và Change Facts đã lưu"""
    return await call("GET", f"/bo-thay-doi/{change_set_id}", config)


@tool
async def lint_requirement(requirement_version_id: Annotated[str, Field(description="Mã Requirement Version")], config: RunnableConfig = None) -> str:
    """Kiểm tra chất lượng Requirement Version"""
    return await call("POST", f"/phien-ban-yeu-cau/{requirement_version_id}/ai/kiem-tra", config)


@tool
async def get_traceability_links(project_id: Annotated[str, Field(description="Mã Project")], config: RunnableConfig = None) -> str:
    """Lấy Traceability Links trong Project"""
    return await call("GET", f"/du-an/{project_id}/truy-vet", config)


@tool
async def search_related_testcases(project_id: Annotated[str, Field(description="Mã Project")], query: Annotated[str, Field(description="Nội dung liên quan")], config: RunnableConfig = None) -> str:
    """Tìm Test Case liên quan trong Project"""
    return await call("GET", f"/du-an/{project_id}/ca-kiem-thu?q={query}", config)


@tool
async def generate_test_scenarios(requirement_version_id: Annotated[str, Field(description="Mã Requirement Version")], instruction: Annotated[str, Field(description="Chỉ dẫn sinh scenario")] = "", config: RunnableConfig = None) -> str:
    """Sinh Test Scenario Draft từ Requirement Version"""
    return await call("POST", f"/phien-ban-yeu-cau/{requirement_version_id}/ai/sinh-kich-ban", config, {"instruction": instruction})


@tool
async def generate_testcases(requirement_version_id: Annotated[str, Field(description="Mã Requirement Version")], instruction: Annotated[str, Field(description="Chỉ dẫn sinh Test Case")] = "", config: RunnableConfig = None) -> str:
    """Sinh Test Case Draft có cấu trúc từ Requirement Version"""
    return await call("POST", f"/phien-ban-yeu-cau/{requirement_version_id}/ai/sinh-ca-kiem-thu", config, {"instruction": instruction})


@tool
async def lint_testcase(test_case_draft_id: Annotated[str, Field(description="Mã Test Case Draft")], config: RunnableConfig = None) -> str:
    """Kiểm tra chất lượng Test Case Draft"""
    return await call("POST", f"/ban-nhap-ca-kiem-thu/{test_case_draft_id}/kiem-tra", config)


@tool
async def find_duplicate_testcases(project_id: Annotated[str, Field(description="Mã Project")], config: RunnableConfig = None) -> str:
    """Tìm Test Case trùng hoặc gần trùng"""
    return await call("GET", f"/du-an/{project_id}/ca-kiem-thu/trung-lap", config)


@tool
async def calculate_coverage(project_id: Annotated[str, Field(description="Mã Project")], config: RunnableConfig = None) -> str:
    """Tính deterministic coverage cho Project"""
    return await call("GET", f"/du-an/{project_id}/do-phu", config)


@tool
async def analyze_change_impact(change_set_id: Annotated[str, Field(description="Mã Change Set")], config: RunnableConfig = None) -> str:
    """Phân tích ảnh hưởng của Change Set"""
    return await call("POST", f"/bo-thay-doi/{change_set_id}/phan-tich-anh-huong", config)


@tool
async def propose_testcase_revision(impact_analysis_id: Annotated[str, Field(description="Mã Impact Analysis")], config: RunnableConfig = None) -> str:
    """Sinh proposal sửa Test Case chờ duyệt"""
    return await call("POST", f"/phan-tich-anh-huong/{impact_analysis_id}/de-xuat-bao-tri", config)


@tool
async def propose_new_testcase(impact_analysis_id: Annotated[str, Field(description="Mã Impact Analysis")], config: RunnableConfig = None) -> str:
    """Sinh proposal tạo Test Case mới chờ duyệt"""
    return await call("POST", f"/phan-tich-anh-huong/{impact_analysis_id}/de-xuat-bao-tri", config)


@tool
async def propose_obsolete_testcase(impact_analysis_id: Annotated[str, Field(description="Mã Impact Analysis")], config: RunnableConfig = None) -> str:
    """Sinh proposal obsolete Test Case chờ duyệt"""
    return await call("POST", f"/phan-tich-anh-huong/{impact_analysis_id}/de-xuat-bao-tri", config)


@tool
async def suggest_regression_scope(change_set_id: Annotated[str, Field(description="Mã Change Set")], config: RunnableConfig = None) -> str:
    """Đề xuất phạm vi regression từ Change Set"""
    return await call("POST", f"/bo-thay-doi/{change_set_id}/de-xuat-hoi-quy", config)


@tool
async def get_execution_history(project_id: Annotated[str, Field(description="Mã Project")], config: RunnableConfig = None) -> str:
    """Lấy lịch sử Test Run và execution trong Project"""
    return await call("GET", f"/du-an/{project_id}/lan-chay-kiem-thu", config)


@tool
async def get_bug_history(project_id: Annotated[str, Field(description="Mã Project")], config: RunnableConfig = None) -> str:
    """Lấy lịch sử Defect trong Project"""
    return await call("GET", f"/du-an/{project_id}/loi", config)


@tool
async def link_bug_candidates(defect_id: Annotated[str, Field(description="Mã Defect")], config: RunnableConfig = None) -> str:
    """Tìm trace candidate cho Defect"""
    return await call("GET", f"/loi/{defect_id}/ung-vien-truy-vet", config)
