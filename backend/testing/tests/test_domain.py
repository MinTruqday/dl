import asyncio
from datetime import datetime, timezone

import httpx
import pytest
from pydantic import ValidationError

from src.api.api_artifacts import (
    api_case_blueprints,
    create_xlsx,
    parse_openapi,
    parse_postman,
    sanitize_postman,
)
from src.api.execution import frozen_run_scope, frozen_run_scope_hash
from src.api.requirements import (
    atomic_requirement_candidates,
    candidate_fingerprint,
    extract_xlsx_csv,
    prepare_requirement_candidates,
)
from src.core.common import envelope, failure_metadata
from src.domain.schemas import (
    BulkArchiveInput,
    BulkProposalApproveInput,
    BulkTagInput,
    DefectTraceUpdateInput,
    DeviceMatrixCreate,
    DeviceMatrixAssignment,
    ProjectNotificationPreferencePatch,
    ProjectNotificationRulePatch,
    PerformancePlanDraftInput,
    SecurityTestSuggestionInput,
    WebhookSubscriptionCreate,
    TestExecutionPatch as ExecutionPatchSchema,
    TestStepResultInput as StepResultSchema,
)
from src.services import project_knowledge
from src.services.change_analysis import classify_test_impact, semantic_changes
from src.services.linters import (
    duplicate_score,
    lint_test_case,
    requirement_duplicate_score,
    requirement_findings,
)
from src.api.design_suggestions import performance_scenarios, security_candidates
from src.api.automation_scripts import script_template, validate_source
from benchmark.run import evaluate_all


def doc(text):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


def test_not_applicable_result_requires_reason_at_case_and_step_level():
    with pytest.raises(ValidationError):
        ExecutionPatchSchema(
            status="NOT_APPLICABLE",
            note="",
            idempotency_key="not-applicable-case",
        )
    with pytest.raises(ValidationError):
        StepResultSchema(step_id="step-1", status="NOT_APPLICABLE", note="")
    result = ExecutionPatchSchema(
        status="NOT_APPLICABLE",
        note="Không thuộc cấu hình của bản dựng này",
        step_results=[
            StepResultSchema(
                step_id="step-1",
                status="NOT_APPLICABLE",
                note="Bước chỉ dành cho thiết bị di động",
            )
        ],
        idempotency_key="not-applicable-valid",
    )
    assert result.status == "NOT_APPLICABLE"


def test_defect_trace_update_requires_an_explicit_human_change():
    with pytest.raises(ValidationError):
        DefectTraceUpdateInput(expected_revision=1, reason="Đã kiểm tra")
    payload = DefectTraceUpdateInput(
        expected_revision=1,
        reason="Đã kiểm tra bằng chứng",
        linked_test_case_version_id=None,
    )
    assert "linked_test_case_version_id" in payload.model_fields_set


def test_bulk_mutations_support_preview_and_replay_metadata():
    tag = BulkTagInput(
        artifact_type="test_case",
        ids=["TC-1"],
        add_tags=["smoke"],
        preview=True,
        idempotency_key="bulk-tag-preview",
    )
    assert tag.preview is True
    archive = BulkArchiveInput(
        artifact_type="test_case",
        ids=["TC-1"],
        reason="Đã được thay thế",
        preview=True,
        idempotency_key="bulk-archive-preview",
    )
    assert archive.idempotency_key == "bulk-archive-preview"
    approval = BulkProposalApproveInput(
        proposal_ids=["MP-1"],
        review_note="Đã đối chiếu mục tiêu và phiên bản nền",
        preview=True,
        idempotency_key="bulk-approval-preview",
    )
    assert approval.preview is True


def test_device_matrix_requires_unique_profiles_and_valid_assignment_target():
    with pytest.raises(ValidationError):
        DeviceMatrixCreate(
            name="Thiết bị trình duyệt",
            profiles=[
                {
                    "key": "chrome-desktop",
                    "name": "Chrome máy tính",
                    "device_type": "desktop",
                    "operating_system": "Linux",
                },
                {
                    "key": "chrome-desktop",
                    "name": "Chrome máy tính khác",
                    "device_type": "desktop",
                    "operating_system": "Windows",
                },
            ],
        )
    assignment = DeviceMatrixAssignment(
        target_type="test_run",
        target_id="TRUN-1",
        expected_target_revision=1,
        profile_keys=["chrome-desktop"],
    )
    assert assignment.target_type == "test_run"


def test_project_notification_inputs_validate_channels_and_quiet_hours():
    rules = ProjectNotificationRulePatch(
        expected_revision=0,
        enabled_events=["DEFECT_CREATED"],
        channels=["in_app", "email"],
        target_roles=["QA_LEAD", "TESTER"],
        escalation_minutes=30,
    )
    assert rules.escalation_minutes == 30
    preferences = ProjectNotificationPreferencePatch(
        expected_revision=0,
        digest_frequency="daily",
        channels=["in_app"],
        quiet_hours_start="22:00",
        quiet_hours_end="07:00",
    )
    assert preferences.digest_frequency == "daily"
    with pytest.raises(ValidationError):
        ProjectNotificationPreferencePatch(
            expected_revision=0,
            quiet_hours_start="25:00",
        )


def test_specialized_design_drafts_never_claim_execution_or_approval():
    security_payload = SecurityTestSuggestionInput(
        categories=["authorization", "session"],
        idempotency_key="security-design-1",
    )
    candidates = security_candidates(security_payload.categories, [])
    assert [item["status"] for item in candidates] == ["SUGGESTED", "SUGGESTED"]
    assert all(item["origin"] == "ai_assisted_draft" for item in candidates)
    performance_payload = PerformancePlanDraftInput(
        name="Tải đăng nhập",
        workload_types=["baseline", "spike", "soak"],
        target_virtual_users=100,
        duration_minutes=30,
        idempotency_key="performance-design-1",
    )
    scenarios = performance_scenarios(performance_payload)
    assert scenarios[0]["virtual_users"] == 25
    assert scenarios[1]["virtual_users"] == 200
    assert scenarios[2]["duration_minutes"] == 240


def test_webhook_subscription_accepts_only_platform_references():
    value = WebhookSubscriptionCreate(
        name="Thông báo lỗi mới",
        endpoint_reference="endpoint://platform/webhook-primary",
        secret_reference="secret://platform/webhook-primary",
        events=["DEFECT_CREATED"],
    )
    assert value.enabled is True
    with pytest.raises(ValidationError):
        WebhookSubscriptionCreate(
            name="Điểm cuối thô",
            endpoint_reference="https://example.test/hook",
            secret_reference="raw-secret",
            events=["DEFECT_CREATED"],
        )


def test_automation_script_templates_use_environment_placeholders_and_reject_raw_secrets():
    version = {"title": "Đăng nhập hợp lệ", "test_case_key": "TC-001"}
    playwright = script_template("playwright", "typescript", version)
    selenium = script_template("selenium", "python", version)
    assert "process.env.BASE_URL" in playwright
    assert "os.environ['BASE_URL']" in selenium
    assert validate_source(playwright) == playwright
    with pytest.raises(Exception):
        validate_source('const password = "plain-password";')


def test_frozen_run_scope_fingerprint_ignores_resume_metadata_and_detects_scope_changes():
    run = {
        "test_plan_id": "PLAN-1",
        "test_suite_ids": ["SUITE-1"],
        "test_case_version_ids": ["TCV-1", "TCV-2"],
        "environment": "staging",
        "release": "1.0",
        "build": "100",
        "device_matrix_snapshot": {
            "profile_keys": ["chrome-desktop"],
            "updated_at": datetime(2026, 9, 2, 8, 30, tzinfo=timezone.utc),
        },
        "last_resumed_by": "USER-1",
    }
    initial = frozen_run_scope_hash(frozen_run_scope(run))
    run["last_resumed_by"] = "USER-2"
    assert frozen_run_scope_hash(frozen_run_scope(run)) == initial
    run["test_case_version_ids"] = ["TCV-1"]
    assert frozen_run_scope_hash(frozen_run_scope(run)) != initial


def test_requirement_linter_returns_structured_findings():
    findings = requirement_findings(
        {
            "content_doc": doc("Hệ thống phải nhanh và dễ dùng"),
            "plain_text_projection": "Hệ thống phải nhanh và dễ dùng",
            "actors": [],
            "acceptance_criterion_ids": [],
        }
    )
    rules = {item["rule_id"] for item in findings}
    assert {"AMBIGUOUS_TERM", "MISSING_ACTOR", "MISSING_ACCEPTANCE_CRITERIA"} <= rules
    assert all("suggestion" in item and "severity" in item for item in findings)


def test_requirement_document_extraction_is_atomic_and_preserves_source_spans():
    content = "Người dùng đăng nhập bằng email. Sau 5 lần sai tài khoản bị khóa 15 phút."
    candidates = atomic_requirement_candidates(
        {
            "_id": "RDOC-1",
            "filename": "login.md",
            "format": "md",
            "content_hash": "source-hash",
            "normalized_content": content,
        }
    )
    assert len(candidates) == 2
    assert candidates[0]["title"] == "Người dùng đăng nhập bằng email."
    assert candidates[1]["title"] == "Sau 5 lần sai tài khoản bị khóa 15 phút."
    for candidate in candidates:
        source = candidate["source_refs"][0]
        assert content[source["source_start"] : source["source_end"]] == candidate["title"]
        assert source["requirement_document_id"] == "RDOC-1"


def test_requirement_candidates_receive_stable_identity_and_provenance_fingerprint():
    candidates = prepare_requirement_candidates(
        "RIMP-1",
        [
            {
                "title": "Đăng nhập",
                "content_doc": doc("Người dùng đăng nhập"),
                "source_refs": [{"requirement_document_id": "RDOC-1", "source_start": 0}],
            }
        ],
    )
    replayed = prepare_requirement_candidates("RIMP-1", candidates)
    assert candidates[0]["candidate_id"] == "RIMP-1-CAND-1"
    assert replayed[0]["candidate_id"] == candidates[0]["candidate_id"]
    assert candidates[0]["candidate_status"] == "ACTIVE"
    assert candidate_fingerprint(replayed[0]) == candidate_fingerprint(candidates[0])
    assert candidate_fingerprint({**candidates[0], "title": "Đăng nhập mới"}) != candidate_fingerprint(candidates[0])


def test_requirement_duplicate_score_distinguishes_exact_semantic_and_unrelated_content():
    baseline = {
        "title": "Khóa tài khoản sau nhiều lần đăng nhập sai",
        "content_doc": doc("Khi nhập sai mật khẩu năm lần thì tài khoản phải bị khóa"),
        "business_rules": ["Khóa sau năm lần sai"],
        "acceptance_criteria": [{"content_doc": doc("Tài khoản bị khóa ở lần sai thứ năm")}],
    }
    exact_score, exact_reasons = requirement_duplicate_score(baseline, {**baseline})
    semantic_score, semantic_reasons = requirement_duplicate_score(
        baseline,
        {
            **baseline,
            "title": "Khóa người dùng khi đăng nhập sai nhiều lần",
            "content_doc": doc("Khi mật khẩu sai năm lần thì hệ thống phải khóa tài khoản"),
        },
    )
    unrelated_score, _ = requirement_duplicate_score(
        baseline,
        {
            "title": "Xuất báo cáo kiểm thử",
            "content_doc": doc("Người quản lý tải báo cáo CSV theo kỳ"),
            "business_rules": [],
            "acceptance_criteria": [],
        },
    )
    assert exact_score == 1
    assert exact_reasons == ["Nội dung Requirement trùng khớp hoàn toàn"]
    assert semantic_score > unrelated_score
    assert semantic_reasons


def test_test_case_linter_blocks_missing_expected_and_trace():
    findings = lint_test_case(
        {
            "preconditions_doc": doc(""),
            "expected_result_doc": doc(""),
            "steps": [],
            "test_data": {},
            "requirement_version_ids": [],
            "acceptance_criterion_ids": [],
        }
    )
    rules = {item["rule_id"] for item in findings}
    assert {"TCQ-001", "TCQ-002", "TCQ-005", "TCQ-009"} <= rules


def test_duplicate_score_uses_text_trace_and_structure():
    value = {
        "title": "Phone 11 digits",
        "preconditions_doc": doc("User exists"),
        "steps": [{"action_doc": doc("Enter 11 digits"), "expected_doc": doc("Rejected")}],
        "expected_result_doc": doc("Rejected"),
        "requirement_version_ids": ["REQV-1"],
        "acceptance_criterion_ids": ["AC-1"],
    }
    score, reasons = duplicate_score(value, {**value})
    assert score == 1
    assert len(reasons) == 3


def test_semantic_diff_detects_boundary_change():
    before = {"_id": "REQV-1", "plain_text_projection": "Phone exactly 10 digits"}
    after = {"_id": "REQV-2", "plain_text_projection": "Phone accepts 10 or 11 digits"}
    changes = semantic_changes(before, after)
    assert changes[0]["type"] == "MODIFIED_BOUNDARY"
    assert changes[0]["before"]["values"] == [10]
    assert changes[0]["after"]["values"] == [10, 11]


def test_impact_marks_new_boundary_test_for_update():
    changes = [
        {
            "type": "MODIFIED_BOUNDARY",
            "before": {"values": [10]},
            "after": {"values": [10, 11]},
        }
    ]
    result = classify_test_impact(
        {
            "_id": "TCV-1",
            "test_case_id": "TC-1",
            "test_case_key": "TC-PHONE-003",
            "plain_text_projection": "Enter 11 digits Expected validation error",
        },
        changes,
        True,
    )
    assert result["classification"] == "NEEDS_UPDATE"
    assert result["confidence"] >= 0.9
    assert result["evidence"][0]["direct_trace"] is True


def test_impact_preserves_unmodified_boundary_cases():
    changes = [{"type": "MODIFIED_BOUNDARY", "before": {"values": [10]}, "after": {"values": [10, 11]}}]
    for value in (9, 10):
        result = classify_test_impact({"_id": f"TCV-{value}", "test_case_id": f"TC-{value}", "test_case_key": f"TC-{value}", "plain_text_projection": f"Phone {value} digits"}, changes, True)
        assert result["classification"] == "STILL_VALID"


def test_openapi_parser_and_generator_use_only_documented_responses():
    operations = parse_openapi({"openapi": "3.1.0", "paths": {"/users/{id}": {"get": {"summary": "Read user", "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "ok"}, "401": {"description": "unauthorized"}, "404": {"description": "missing"}}}}}})
    cases = api_case_blueprints(operations[0])
    assert {item["category"] for item in cases} == {"success", "required_missing", "auth", "not_found"}
    assert all("403" not in item["expected"] and "409" not in item["expected"] for item in cases)


def test_postman_parser_removes_secret_values_and_names():
    operations = parse_postman({"variable": [{"key": "baseUrl", "value": "https://example.test"}, {"key": "api_token", "value": "secret-value"}], "item": [{"name": "Users", "request": {"method": "GET", "url": {"raw": "{{baseUrl}}/users?token=secret-value"}, "header": [{"key": "Authorization", "value": "Bearer secret-value"}, {"key": "Accept", "value": "application/json"}]}}]})
    assert operations[0]["path"] == "{{baseUrl}}/users"
    assert operations[0]["header_names"] == ["Accept"]
    assert operations[0]["variable_names"] == ["baseUrl"]
    assert "secret-value" not in str(operations[0])


def test_evaluation_harness_meets_recall_gate():
    report = evaluate_all()
    assert report["aggregate"]["recall"] >= 0.9
    assert report["aggregate"]["f1"] >= 0.9
    assert report["versions"]["prompt_version"] == "qa-v1"


def test_xlsx_export_round_trips_unicode_and_columns():
    content = create_xlsx([["test_case_key", "title"], ["TC-001", "Kiểm thử đăng nhập"]])
    parsed = extract_xlsx_csv(content)
    assert "test_case_key,title" in parsed
    assert "TC-001,Kiểm thử đăng nhập" in parsed


def test_postman_runner_copy_replaces_raw_secrets_with_placeholders():
    value = {
        "variable": [{"key": "api_key", "value": "raw-api-key"}],
        "item": [
            {
                "request": {
                    "header": [{"key": "Authorization", "value": "Bearer raw-token"}],
                    "url": {"raw": "https://example.test/path?token=raw-token"},
                }
            }
        ],
    }
    serialized = str(sanitize_postman(value))
    assert "raw-api-key" not in serialized
    assert "raw-token" not in serialized
    assert "VERIQ_SECRET" in serialized


def test_v2_failure_envelope_preserves_recovery_state():
    metadata = failure_metadata("KNOWLEDGE_UNAVAILABLE", 503)
    result = envelope(None, **metadata)
    assert result["status"] == "FAILED"
    assert result["error_code"] == "KNOWLEDGE_UNAVAILABLE"
    assert result["retryable"] is True
    assert result["state_after_failure"] == "RETRYABLE_FAILURE"
    assert result["meta"]["operation"]["status"] == "FAILED"


def test_operation_envelope_exposes_operation_id_in_metadata():
    result = envelope({"status": "QUEUED"}, operation_id="OP-001")
    assert result["meta"]["operation_id"] == "OP-001"


def test_knowledge_failure_returns_degraded_mode(monkeypatch):
    class BrokenClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, path, headers=None, json=None):
            raise httpx.ConnectError("knowledge down")

    monkeypatch.setattr(project_knowledge.httpx, "AsyncClient", lambda **kwargs: BrokenClient())
    result = asyncio.run(project_knowledge.search_project_with_status("project-1", "query", [], 10))
    assert result == {"items": [], "degraded_mode": "DEGRADED_KNOWLEDGE", "error_code": "KNOWLEDGE_UNAVAILABLE"}
