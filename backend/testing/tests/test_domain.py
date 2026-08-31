import asyncio

import httpx

from src.api.api_artifacts import api_case_blueprints, create_xlsx, parse_openapi, parse_postman
from src.api.requirements import atomic_requirement_candidates, extract_xlsx_csv
from src.core.common import envelope, failure_metadata
from src.services import project_knowledge
from src.services.change_analysis import classify_test_impact, semantic_changes
from src.services.linters import duplicate_score, lint_test_case, requirement_findings
from benchmark.run import evaluate_all


def doc(text):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


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


def test_v2_failure_envelope_preserves_recovery_state():
    metadata = failure_metadata("KNOWLEDGE_UNAVAILABLE", 503)
    result = envelope(None, **metadata)
    assert result["status"] == "FAILED"
    assert result["error_code"] == "KNOWLEDGE_UNAVAILABLE"
    assert result["retryable"] is True
    assert result["state_after_failure"] == "RETRYABLE_FAILURE"
    assert result["meta"]["operation"]["status"] == "FAILED"


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
