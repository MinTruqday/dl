from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.core.auth import ProjectRole, permissions_for_role
from src.domain.test_monitoring import ControlActionCreate, ExitCriterionDefinition, source_fingerprint
from src.services.exit_criteria_service import evaluate_exit_criteria, quality_gate_status
from src.services.test_monitoring_service import build_metrics


def test_exit_criteria_are_deterministic_and_support_percent_ratios():
    definitions = [
        {"criterion_id": "E1", "criterion": "Thực thi tối thiểu", "type": "EXECUTION_PERCENT_MIN", "threshold": 95},
        {"criterion_id": "E2", "criterion": "Tỷ lệ đạt", "key": "pass_rate", "value": 0.9},
        {"criterion_id": "E3", "criterion": "Không có blocker", "type": "OPEN_BLOCKER_MAX", "threshold": 0},
        {"criterion_id": "E4", "criterion": "Các run bắt buộc hoàn tất", "type": "REQUIRED_RUNS_COMPLETED", "threshold": ["RUN-1", "RUN-2"]},
    ]
    metrics = {"execution_percent": 96, "pass_rate": 91, "open_blocker": 1}
    first = evaluate_exit_criteria(definitions, metrics, ["RUN-1"])
    second = evaluate_exit_criteria(definitions, metrics, ["RUN-1"])
    assert first == second
    assert [item["status"] for item in first] == ["PASS", "PASS", "FAIL", "FAIL"]
    assert quality_gate_status(first) == "FAIL"


def test_unknown_quality_target_requires_manual_evaluation():
    result = evaluate_exit_criteria([{"key": "business_readiness", "value": "owner decision"}], {}, [])
    assert result[0]["type"] == "CUSTOM_MANUAL_GATE"
    assert result[0]["status"] == "MANUAL_REQUIRED"
    assert quality_gate_status(result) == "MANUAL_REQUIRED"


def test_monitoring_source_fingerprint_is_order_independent_for_canonical_objects():
    left = {"plan": {"revision": 2, "id": "TP-1"}, "runs": [{"id": "RUN-1"}]}
    right = {"runs": [{"id": "RUN-1"}], "plan": {"id": "TP-1", "revision": 2}}
    assert source_fingerprint(left) == source_fingerprint(right)
    right["runs"][0]["status"] = "COMPLETED"
    assert source_fingerprint(left) != source_fingerprint(right)


def test_monitoring_contract_requires_owner_due_date_and_decision_reason():
    valid = {
        "snapshot_id": "MONS-1",
        "type": "BLOCK_RELEASE",
        "title": "Tạm dừng phát hành",
        "owner_id": "QA-1",
        "due_at": "2026-09-30T12:00:00Z",
        "decision_reason": "Còn lỗi blocker đang mở",
    }
    assert ControlActionCreate(**valid).priority == "MEDIUM"
    for field in ("owner_id", "due_at", "decision_reason"):
        invalid = dict(valid)
        invalid.pop(field)
        with pytest.raises(ValidationError):
            ControlActionCreate(**invalid)


def test_monitoring_permissions_match_v5_role_boundaries():
    lead = permissions_for_role(ProjectRole.QA_LEAD)
    tester = permissions_for_role(ProjectRole.TESTER)
    analyst = permissions_for_role(ProjectRole.BA)
    developer = permissions_for_role(ProjectRole.DEVELOPER)
    viewer = permissions_for_role(ProjectRole.VIEWER)
    assert {"testmonitor.read", "testmonitor.snapshot.create", "testmonitor.control.create", "testmonitor.control.assign", "testmonitor.control.update", "testmonitor.exit_criteria.override", "testmonitor.report.create"} <= lead
    assert {"testmonitor.read", "testmonitor.control.create", "testmonitor.control.update"} <= tester
    assert "testmonitor.snapshot.create" not in tester
    assert "testmonitor.control.assign" not in tester
    assert "testmonitor.exit_criteria.override" not in tester | analyst | developer | viewer
    assert all("testmonitor.read" in role for role in (analyst, developer, viewer))


def test_required_run_criterion_rejects_non_list_threshold():
    with pytest.raises(ValidationError):
        ExitCriterionDefinition(criterion_id="E1", criterion="Runs", type="REQUIRED_RUNS_COMPLETED", threshold=1)


def test_monitoring_reports_api_and_nfr_coverage_when_applicable():
    sources = {
        "results": [],
        "versions": [
            {
                "_id": "TCV-1",
                "requirement_version_ids": [],
                "acceptance_criterion_ids": [],
                "test_condition_ids": ["TCON-1"],
                "source_evidence": [{"artifact_type": "api_operation", "artifact_id": "APIOP-1"}],
            }
        ],
        "requirements": [],
        "criteria": [],
        "conditions": [{"_id": "TCON-1", "risk": "HIGH"}],
        "api_operations": [{"_id": "APIOP-1"}, {"_id": "APIOP-2"}],
        "nfr_plans": [{"_id": "NFR-1", "test_condition_ids": ["TCON-1"], "test_case_version_ids": []}],
        "defects": [],
        "runs": [],
        "since": None,
        "expected_completion": None,
        "actual_effort": None,
        "changed_requirements": 0,
        "stale_testcases": 0,
        "impact_pending": 0,
        "proposal_pending": 0,
        "environment_incidents": [],
    }
    metrics = build_metrics({}, sources, datetime.now(timezone.utc))
    assert metrics["api_coverage"] == 50
    assert metrics["nfr_coverage"] == 100
