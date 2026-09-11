import asyncio

import pytest

from src.api import inference
from src.core.security.guardrails import guardrails_engine
from src.schemas.inference import (
    AutomationScriptOutput,
    CausalHypothesesOutput,
    CompletionReportNarrativeOutput,
    GeneratedCasesOutput,
    PerformanceSuggestionsOutput,
    ProjectQuestionOutput,
    SecuritySuggestionsOutput,
    StatusReportNarrativeOutput,
    LessonsLearnedClustersOutput,
    TestingAssistanceRequest as AssistanceRequest,
)


def request(capability):
    return AssistanceRequest(
        capability=capability,
        project_id="PRJ-1",
        instruction="Tạo kết quả cụ thể",
        evidence=[
            {
                "artifact_type": "requirement_version",
                "artifact_version_id": "REQV-1",
                "text": "Số điện thoại phải có đúng 10 chữ số",
            }
        ],
    )


def test_project_artifact_ids_are_not_classified_as_credentials():
    assessment = guardrails_engine.inspect_input(
        '{"project_id": "PRJ-d3ea810846444793998b2fd4c803e4c1", "artifact_version_id": "TCV-b2da9d19a7574bab85cb399f1b4ddce0"}'
    )

    assert assessment["is_safe"] is True
    assert "[REDACTED]" not in assessment["sanitized_text"]


def test_nested_project_artifact_ids_remain_safe_in_testing_evidence():
    evidence = [
        {
            "artifact_type": "test_completion_report",
            "artifact_id": "TCP-d3ea810846444793998b2fd4c803e4c1",
            "text": '{"defect_id": "DEF-b2da9d19a7574bab85cb399f1b4ddce0", "environment_id": "ENV-a2da9d19a7574bab85cb399f1b4ddce1"}',
        }
    ]

    assessment = guardrails_engine.inspect_input(inference.testing_evidence_text(evidence))

    assert assessment["is_safe"] is True
    assert "[REDACTED]" not in assessment["sanitized_text"]


@pytest.mark.parametrize(
    ("capability", "expected_schema", "payload"),
    [
        (
            "project_question",
            ProjectQuestionOutput,
            {
                "capability": "project_question",
                "answer": "Số điện thoại phải có đúng 10 chữ số",
                "evidence_refs": ["REQV-1"],
                "confidence": 0.9,
                "warnings": [],
            },
        ),
        (
            "test_generation",
            GeneratedCasesOutput,
            {
                "capability": "test_generation",
                "suggestions": [
                    {
                        "title": "Kiểm tra số điện thoại hợp lệ",
                        "category": "happy_path",
                        "objective": "Xác minh số có 10 chữ số",
                        "preconditions": "Biểu mẫu đã mở",
                        "steps": [
                            {
                                "action": "Nhập 0912345678",
                                "expected": "Dữ liệu được chấp nhận",
                                "test_data": {},
                            }
                        ],
                        "expected": "Biểu mẫu được gửi",
                        "acceptance_criterion_ids": [],
                    }
                ],
                "evidence_refs": ["REQV-1"],
                "confidence": 0.8,
                "warnings": [],
            },
        ),
        (
            "security_test_generation",
            SecuritySuggestionsOutput,
            {
                "capability": "security_test_generation",
                "suggestions": [
                    {
                        "category": "input_validation",
                        "title": "Từ chối ký tự không phải số",
                        "preconditions": ["Biểu mẫu đã mở"],
                        "action": "Nhập ký tự chữ",
                        "expected": "Hệ thống từ chối dữ liệu",
                        "requirement_version_ids": ["REQV-1"],
                    }
                ],
                "evidence_refs": ["REQV-1"],
                "confidence": 0.8,
                "warnings": [],
            },
        ),
        (
            "performance_plan_generation",
            PerformanceSuggestionsOutput,
            {
                "capability": "performance_plan_generation",
                "suggestions": [
                    {
                        "workload_type": "load",
                        "title": "Tải nhập số điện thoại",
                        "virtual_users": 100,
                        "requests_per_second": 50,
                        "duration_minutes": 30,
                        "ramp_pattern": "Tăng dần trong 5 phút",
                        "actions": ["Gửi biểu mẫu"],
                        "expected": "Đáp ứng ngưỡng đã khai báo",
                    }
                ],
                "evidence_refs": ["REQV-1"],
                "confidence": 0.8,
                "warnings": [],
            },
        ),
        (
            "automation_script_generation",
            AutomationScriptOutput,
            {
                "capability": "automation_script_generation",
                "suggestions": [
                    {
                        "source": "test('phone', async ({ page }) => { await page.fill('#phone', '0912345678') })",
                        "secret_placeholders": [],
                    }
                ],
                "evidence_refs": ["REQV-1"],
                "confidence": 0.8,
                "warnings": [],
            },
        ),
        (
            "causal_analysis",
            CausalHypothesesOutput,
            {
                "capability": "causal_analysis",
                "suggestions": [
                    {
                        "root_cause_category": "CONFIGURATION",
                        "hypothesis": "Cấu hình môi trường không đồng nhất",
                        "contributing_factors": ["Thiếu kiểm tra cấu hình trước triển khai"],
                        "five_whys": ["Cấu hình không được xác minh tự động"],
                        "missing_test_conditions": ["Kiểm tra cấu hình môi trường"],
                        "missing_test_cases": ["Từ chối chạy khi cấu hình sai"],
                        "evidence_refs": ["REQV-1"],
                        "confidence": 0.7,
                    }
                ],
                "evidence_refs": ["REQV-1"],
                "confidence": 0.7,
                "warnings": [],
            },
        ),
        (
            "status_report_narrative",
            StatusReportNarrativeOutput,
            {
                "capability": "status_report_narrative",
                "suggestions": [{"executive_summary": "Tổng quan kiểm thử", "progress_summary": "Tiến độ kiểm thử", "coverage_summary": "Độ phủ kiểm thử", "defect_summary": "Tình trạng lỗi", "forecast": "Dự báo kỳ tiếp theo", "recommendation": "CONTINUE_TESTING"}],
                "evidence_refs": ["REQV-1"],
                "confidence": 0.8,
                "warnings": [],
            },
        ),
        (
            "completion_report_narrative",
            CompletionReportNarrativeOutput,
            {
                "capability": "completion_report_narrative",
                "suggestions": [{"executive_summary": "Tổng kết kiểm thử", "closure_summary": "Tổng kết đóng kiểm thử", "residual_risk_summary": "Tổng kết rủi ro còn lại", "recommendation_rationale": "Cơ sở khuyến nghị"}],
                "evidence_refs": ["REQV-1"],
                "confidence": 0.8,
                "warnings": [],
            },
        ),
        (
            "lessons_learned_clustering",
            LessonsLearnedClustersOutput,
            {
                "capability": "lessons_learned_clustering",
                "suggestions": [{"theme": "Môi trường", "category": "IMPROVEMENT", "summary": "Chuẩn hóa kiểm tra môi trường", "source_indices": [0], "improvement_candidates": ["Tự động hóa kiểm tra"]}],
                "evidence_refs": ["REQV-1"],
                "confidence": 0.8,
                "warnings": [],
            },
        ),
    ],
)
def test_testing_assistance_uses_capability_schema(
    monkeypatch, capability, expected_schema, payload
):
    observed = {}

    async def fake_structured(prompt, schema, **kwargs):
        observed["schema"] = schema
        observed["max_tokens"] = kwargs["max_tokens"]
        return schema.model_validate(payload)

    monkeypatch.setattr(inference, "structured", fake_structured)
    result = asyncio.run(inference.testing_assistance(request(capability)))

    assert observed["schema"] is expected_schema
    assert observed["max_tokens"] == (256 if capability == "project_question" else 3072)
    assert result.status == "SUCCESS"
    assert result.degraded_mode is None
    assert result.model["provider"] == "primary"
    assert result.evidence_refs == ["REQV-1"]
