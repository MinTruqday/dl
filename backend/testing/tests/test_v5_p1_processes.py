from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.core.auth import ProjectRole, permissions_for_role
from src.domain.causal_analysis import CausalAnalysisCreate, PreventionActionPatch
from src.domain.environment_incident import EnvironmentIncidentCreate, EnvironmentIncidentTransition
from src.domain.measurement import MeasurementDefinitionCreate, validate_threshold_order
from src.domain.non_functional_test import ExternalTestEvidenceImport, NonFunctionalTestPlanCreate
from src.domain.quality_evaluation import QualityEvaluationCreate, QualityWaiverDecision
from src.domain.review_session import ReviewFindingPatch, ReviewSessionCreate
from src.services.measurement import ratio


def test_formal_review_contract_requires_distinct_moderator_and_reviewer():
    payload = {"review_type": "TEST_CASE_REVIEW", "artifact_type": "TEST_CASE", "artifact_id": "TC-1", "artifact_version_id": "TCV-1", "objective": "Đánh giá đầy đủ", "checklist_version": "V5", "moderator_id": "U-1", "author_id": "U-2", "reviewers": ["U-3"]}
    assert ReviewSessionCreate(**payload).reviewers == ["U-3"]
    with pytest.raises(ValidationError):
        ReviewSessionCreate(**{**payload, "reviewers": ["U-1"]})


def test_formal_review_finding_requires_resolution_when_closed():
    with pytest.raises(ValidationError):
        ReviewFindingPatch(expected_revision=1, status="RESOLVED", resolution="")
    assert ReviewFindingPatch(expected_revision=1, status="RESOLVED", resolution="Đã sửa").status == "RESOLVED"


def test_measurement_definition_and_formula_are_explicit():
    value = MeasurementDefinitionCreate(key="PASS_RATE", name="Tỷ lệ đạt", objective="Theo dõi chất lượng", formula="pass / decisive * 100", unit="%", data_sources=["test_results"], aggregation="RATIO", period="RELEASE", target=95, warning_threshold=90, critical_threshold=80, owner_role="QA_LEAD")
    assert value.formula == "pass / decisive * 100"
    assert ratio(9, 10) == 90
    assert ratio(0, 0) is None
    lower_is_better = MeasurementDefinitionCreate(key="BLOCKED_RATE", name="Tỷ lệ bị chặn", objective="Giảm kết quả bị chặn", formula="blocked / decisive * 100", unit="%", data_sources=["test_results"], aggregation="RATIO", period="RELEASE", target=2, warning_threshold=5, critical_threshold=10, owner_role="QA_LEAD")
    assert lower_is_better.critical_threshold == 10
    with pytest.raises(ValidationError):
        MeasurementDefinitionCreate(key="BLOCKED_RATE", name="Tỷ lệ bị chặn", objective="Giảm kết quả bị chặn", formula="blocked / decisive * 100", unit="%", data_sources=["test_results"], aggregation="RATIO", period="RELEASE", target=10, warning_threshold=5, critical_threshold=2, owner_role="QA_LEAD")


def test_measurement_patch_threshold_order_uses_merged_values():
    validate_threshold_order("BLOCKED_RATE", 2, 5, 10)
    with pytest.raises(ValueError):
        validate_threshold_order("BLOCKED_RATE", 2, 12, 10)


def test_quality_evaluation_requires_human_recommendation_rationale_and_sources():
    value = QualityEvaluationCreate(release_id="REL-1", build_id="BLD-1", measurement_snapshot_refs=["MET-1"], monitoring_snapshot_id="MON-1", recommendation="NO_GO", rationale="Gate chưa đạt")
    assert value.recommendation == "NO_GO"
    with pytest.raises(ValidationError):
        QualityEvaluationCreate(release_id="REL-1", build_id="BLD-1", measurement_snapshot_refs=[], monitoring_snapshot_id="MON-1", recommendation="GO", rationale="Đạt")
    with pytest.raises(ValidationError):
        QualityWaiverDecision(expected_revision=1, decision="REJECT", note="")


def test_causal_analysis_and_capa_require_evidence_and_results():
    value = CausalAnalysisCreate(defect_ids=["DEF-1"], problem_statement="Lỗi lặp lại", evidence=["log"], owner_id="U-1")
    assert value.defect_ids == ["DEF-1"]
    with pytest.raises(ValidationError):
        CausalAnalysisCreate(defect_ids=["DEF-1"], problem_statement="Lỗi lặp lại", evidence=[], owner_id="U-1")
    with pytest.raises(ValidationError):
        PreventionActionPatch(expected_revision=1, status="IMPLEMENTED", result="")


def test_environment_incident_requires_resolution_for_terminal_state():
    value = EnvironmentIncidentCreate(environment_id="ENV-1", observed_at=datetime.now(timezone.utc), severity="BLOCKER", type="UNAVAILABLE", description="Môi trường ngừng hoạt động", owner_id="U-1")
    assert value.severity == "BLOCKER"
    with pytest.raises(ValidationError):
        EnvironmentIncidentTransition(expected_revision=1, status="RESOLVED", resolution="")


def test_nfr_plan_requires_trace_and_external_evidence_is_hash_bound():
    with pytest.raises(ValidationError):
        NonFunctionalTestPlanCreate(plan_type="SECURITY_TEST_PLAN", name="Security", objective="Kiểm tra", scope=["API"], approach="Rà soát", test_condition_ids=[], test_case_version_ids=[])
    plan = NonFunctionalTestPlanCreate(plan_type="PERFORMANCE_TEST_PLAN", name="Hiệu năng", objective="Đo tải", scope=["API"], approach="Chạy bên ngoài", test_condition_ids=["TCON-1"])
    assert plan.plan_type == "PERFORMANCE_TEST_PLAN"
    evidence = ExternalTestEvidenceImport(idempotency_key="evidence-123", provider="K6", external_run_ref="run-1", executed_at="2026-09-11T00:00:00Z", evidence_refs=["ATT-1"], result_summary={"p95": 200}, raw_result_hash="a" * 64)
    assert evidence.raw_result_hash == "a" * 64
    with pytest.raises(ValidationError):
        ExternalTestEvidenceImport(idempotency_key="evidence-456", provider="K6", external_run_ref="run-2", executed_at="2026-09-11T00:00:00", evidence_refs=["ATT-2"], result_summary={"p95": 200}, raw_result_hash="b" * 64)


def test_p1_permissions_keep_final_quality_decisions_with_qa_lead():
    lead = permissions_for_role(ProjectRole.QA_LEAD)
    tester = permissions_for_role(ProjectRole.TESTER)
    analyst = permissions_for_role(ProjectRole.BA)
    developer = permissions_for_role(ProjectRole.DEVELOPER)
    viewer = permissions_for_role(ProjectRole.VIEWER)
    assert {"reviewsession.complete", "measurement.manage", "qualityevaluation.approve", "qualityevaluation.waiver.approve", "causalanalysis.approve", "environmentincident.close", "nfrtest.approve"} <= lead
    assert {"reviewsession.create", "measurement.snapshot.create", "qualityevaluation.create", "causalanalysis.create", "environmentincident.create", "nfrtest.manage"} <= tester
    assert "qualityevaluation.review" in analyst
    assert "qualityevaluation.approve" not in tester | analyst | developer | viewer
    assert "causalanalysis.approve" not in tester | analyst | developer | viewer
    assert "environmentincident.close" not in tester | analyst | developer | viewer
    assert all("measurement.read" in role and "qualityevaluation.read" in role for role in (tester, analyst, developer, viewer))


def test_environment_incident_expiry_inputs_preserve_timezone():
    observed = datetime.now(timezone.utc) - timedelta(minutes=5)
    value = EnvironmentIncidentCreate(environment_id="ENV-1", observed_at=observed, severity="MAJOR", type="NETWORK", description="Mất kết nối", owner_id="U-1")
    assert value.observed_at.tzinfo is not None
