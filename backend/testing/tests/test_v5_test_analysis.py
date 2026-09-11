import pytest
from pydantic import ValidationError

from src.core.auth import ProjectRole, permissions_for_role
from src.domain.test_analysis import TestConditionCreate as ConditionCreate
from src.domain.test_analysis import condition_hash


def condition_payload():
    return {
        "title": "Đăng nhập với mật khẩu sai",
        "description_doc": {"type": "doc", "content": []},
        "basis_refs": [
            {
                "artifact_type": "REQUIREMENT_VERSION",
                "artifact_id": "REQ-1",
                "artifact_version_id": "REQV-1",
            }
        ],
        "coverage_item": "Xử lý thông tin xác thực không hợp lệ",
        "test_level": "SYSTEM",
        "test_type": "FUNCTIONAL",
        "risk": "HIGH",
        "priority": "HIGH",
        "technique_candidates": ["equivalence_partitioning"],
        "testability_status": "TESTABLE",
        "analysis_findings": [],
    }


def test_condition_requires_versioned_test_basis_and_valid_tiptap_document():
    value = ConditionCreate(**condition_payload())
    assert value.basis_refs[0].artifact_version_id == "REQV-1"
    invalid = condition_payload()
    invalid["basis_refs"] = []
    with pytest.raises(ValidationError):
        ConditionCreate(**invalid)
    invalid = condition_payload()
    invalid["description_doc"] = {"content": []}
    with pytest.raises(ValidationError):
        ConditionCreate(**invalid)


def test_condition_snapshot_hash_ignores_runtime_state_and_detects_basis_change():
    condition = {
        "_id": "TCON-1",
        "project_id": "PROJECT-1",
        "condition_key": "TCON-001",
        **ConditionCreate(**condition_payload()).model_dump(),
        "basis_snapshots": [{"artifact_id": "REQ-1", "content_hash": "abc"}],
        "revision": 1,
        "status": "DRAFT",
    }
    first = condition_hash(condition)
    condition["revision"] = 9
    condition["status"] = "APPROVED"
    assert condition_hash(condition) == first
    condition["basis_snapshots"][0]["content_hash"] = "def"
    assert condition_hash(condition) != first


def test_condition_permissions_keep_approval_human_and_role_restricted():
    lead = permissions_for_role(ProjectRole.QA_LEAD)
    tester = permissions_for_role(ProjectRole.TESTER)
    analyst = permissions_for_role(ProjectRole.BA)
    developer = permissions_for_role(ProjectRole.DEVELOPER)
    viewer = permissions_for_role(ProjectRole.VIEWER)
    assert {
        "testcondition.read",
        "testcondition.create",
        "testcondition.update",
        "testcondition.review",
        "testcondition.approve",
        "testcondition.archive",
        "testanalysis.run_ai",
        "testanalysis.resolve_finding",
    } <= lead
    assert {"testcondition.read", "testcondition.create", "testcondition.update", "testanalysis.run_ai"} <= tester
    assert {"testcondition.read", "testcondition.create", "testcondition.update", "testanalysis.run_ai"} <= analyst
    assert "testcondition.approve" not in tester | analyst | developer | viewer
    assert "testanalysis.run_ai" not in developer | viewer
