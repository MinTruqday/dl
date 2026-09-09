import asyncio

import pytest

from src.api import inference
from src.core.security.guardrails import guardrails_engine
from src.schemas.inference import (
    AutomationScriptOutput,
    GeneratedCasesOutput,
    PerformanceSuggestionsOutput,
    ProjectQuestionOutput,
    SecuritySuggestionsOutput,
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
