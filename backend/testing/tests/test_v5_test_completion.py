import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.core.auth import ProjectRole, permissions_for_role
from src.core.database import database
from src.domain.test_completion import ResidualRisk, ResidualRiskDecision, TestCompletionCreate as CompletionCreate, completion_hash
from src.services.execution_context import ensure_release_completion_gate
from src.services.test_completion import default_completion_recommendation


def completion_fixture():
    return {
        "_id": "TCP-1",
        "project_id": "PRJ-1",
        "test_plan_id": "TPLAN-1",
        "release_id": "REL-1",
        "build_id": "BLD-1",
        "strategy_version_id": "TSTR-1",
        "scope_snapshot": {"plan_revision": 3, "runs": [{"run_id": "RUN-1", "revision": 4}]},
        "completed_run_ids": ["RUN-1"],
        "execution_summary": {"execution_percent": 100},
        "coverage_summary": {"requirement_coverage": 100},
        "defect_summary": {"open_critical": 0},
        "unresolved_items": [],
        "residual_risks": [],
        "exit_criteria_evaluation": [{"criterion_id": "EXIT-1", "status": "PASS"}],
        "deviations": [],
        "testware_handover": [],
        "archived_artifacts": [],
        "environment_closure": [],
        "lessons_learned": [{"worked": "Rà soát sớm"}],
        "improvement_actions": [],
        "recommendation": "READY_FOR_RELEASE",
        "sign_offs": [],
        "status": "DRAFT",
        "revision": 1,
    }


def test_completion_contract_requires_exact_snapshot_and_build():
    value = CompletionCreate(snapshot_id="MONS-1", build_id="BLD-1")
    assert value.snapshot_id == "MONS-1"
    for field in ("snapshot_id", "build_id"):
        payload = {"snapshot_id": "MONS-1", "build_id": "BLD-1"}
        payload.pop(field)
        with pytest.raises(ValidationError):
            CompletionCreate(**payload)


def test_residual_risk_requires_owner_and_explicit_acceptance_evidence():
    valid = {
        "risk_id": "RISK-1",
        "title": "Sai lệch ở trình duyệt cũ",
        "severity": "MEDIUM",
        "owner_id": "USER-1",
    }
    assert ResidualRisk(**valid).acceptance == "PENDING"
    for missing in ("acceptance_reason", "accepted_by"):
        invalid = {**valid, "acceptance": "ACCEPTED", "acceptance_reason": "Chấp nhận cho bản phát hành", "accepted_by": "USER-2"}
        invalid.pop(missing)
        with pytest.raises(ValidationError):
            ResidualRisk(**invalid)
    assert ResidualRiskDecision(expected_revision=1, acceptance="ACCEPTED", reason="Chấp nhận có chủ đích").acceptance == "ACCEPTED"
    with pytest.raises(ValidationError):
        ResidualRiskDecision(expected_revision=1, acceptance="PENDING", reason="Chưa quyết định")


def test_completion_hash_tracks_content_not_workflow_metadata():
    report = completion_fixture()
    initial = completion_hash(report)
    report.update({"status": "APPROVED", "revision": 7, "approved_by": "QA-1"})
    assert completion_hash(report) == initial
    report["lessons_learned"] = [{"failed": "Phát hiện lỗi quá muộn"}]
    assert completion_hash(report) != initial


def test_completion_recommendation_is_deterministic_and_risk_aware():
    assert default_completion_recommendation("PASS", [], []) == "READY_FOR_RELEASE"
    assert default_completion_recommendation("PASS", [], [{"risk_id": "R-1"}]) == "READY_WITH_RISK"
    assert default_completion_recommendation("MANUAL_REQUIRED", [], []) == "CONTINUE_TESTING"
    assert default_completion_recommendation("PASS", [{"severity": "CRITICAL"}], []) == "NOT_READY"
    assert default_completion_recommendation("FAIL", [], []) == "NOT_READY"


def test_completion_permissions_preserve_qa_lead_final_decision():
    lead = permissions_for_role(ProjectRole.QA_LEAD)
    tester = permissions_for_role(ProjectRole.TESTER)
    analyst = permissions_for_role(ProjectRole.BA)
    developer = permissions_for_role(ProjectRole.DEVELOPER)
    viewer = permissions_for_role(ProjectRole.VIEWER)
    assert {"testcompletion.read", "testcompletion.create", "testcompletion.update", "testcompletion.review", "testcompletion.approve", "testcompletion.close"} <= lead
    assert {"testcompletion.read", "testcompletion.create", "testcompletion.update", "testcompletion.review"} <= tester
    assert "testcompletion.review" in analyst
    assert "testcompletion.approve" not in tester | analyst | developer | viewer
    assert "testcompletion.close" not in tester | analyst | developer | viewer
    assert all("testcompletion.read" in role for role in (analyst, developer, viewer))


class CollectionStub:
    def __init__(self, value):
        self.value = value
        self.query = None

    async def find_one(self, query, projection=None):
        self.query = query
        return self.value


class ClientStub:
    def __init__(self, value):
        self.value = value

    def __getitem__(self, name):
        return self.value


@pytest.mark.asyncio
async def test_release_close_gate_requires_approved_completion(monkeypatch):
    projects = CollectionStub({"settings": {"require_completion_report_before_release_close": True}})
    reports = CollectionStub(None)
    monkeypatch.setattr(database, "client", ClientStub(type("DatabaseStub", (), {"projects": projects, "test_completion_reports": reports})()))
    with pytest.raises(HTTPException) as error:
        await ensure_release_completion_gate("PRJ-1", "REL-1")
    assert error.value.detail == {"code": "COMPLETION_REPORT_REQUIRED"}
    reports.value = {"_id": "TCP-1"}
    await ensure_release_completion_gate("PRJ-1", "REL-1")
    assert reports.query["status"] == {"$in": ["APPROVED", "CLOSED"]}


@pytest.mark.asyncio
async def test_release_close_gate_is_optional(monkeypatch):
    projects = CollectionStub({"settings": {"require_completion_report_before_release_close": False}})
    reports = CollectionStub(None)
    monkeypatch.setattr(database, "client", ClientStub(type("DatabaseStub", (), {"projects": projects, "test_completion_reports": reports})()))
    await ensure_release_completion_gate("PRJ-1", "REL-1")
    assert reports.query is None
