import pytest
from pydantic import ValidationError

from src.domain.schemas import TestPlanCreate as PlanCreate
from src.services.test_plan import plan_snapshot_hash


def base_plan():
    return {
        "project_id": "PROJECT-1",
        "name": "Kế hoạch kiểm thử phát hành 2",
        "strategy_version_id": "TSTR-2",
        "test_level": "SYSTEM",
        "test_approach": "Kiểm thử dựa trên rủi ro",
        "assumptions": ["Môi trường staging tương đương production"],
        "constraints": ["Không dùng dữ liệu khách hàng thật"],
        "dependencies": [{"artifact_type": "release", "artifact_id": "REL-2"}],
        "stakeholders": [{"user_id": "PRODUCT-1", "role": "APPROVER"}],
        "responsibility_matrix": [{"activity": "Test design", "responsible": ["TESTER-1"], "reviewer": ["QA-1"]}],
        "estimation": {"method": "three_point", "planned_effort_hours": 120, "planned_people": 3},
        "schedule": {"planned_start": "2026-09-01", "planned_end": "2026-09-30"},
        "milestones": [{"name": "System test complete", "date": "2026-09-25"}],
        "deliverables": ["Test status report"],
        "tools": ["Playwright"],
        "suspension_criteria": ["Môi trường bị blocker"],
        "resumption_criteria": ["Môi trường được xác minh lại"],
        "monitoring_metrics": [{"key": "execution_progress"}],
        "quality_targets": [{"key": "pass_rate", "operator": ">=", "value": 0.95}],
        "risk_register": [{"risk": "Môi trường không ổn định", "exposure": 9}],
        "communication_plan": {"cadence": "daily", "audience": ["QA_LEAD"]},
    }


def test_extended_test_plan_accepts_management_fields():
    value = PlanCreate(**base_plan())
    assert value.estimation["planned_effort_hours"] == 120
    assert value.responsibility_matrix[0]["activity"] == "Test design"


def test_extended_test_plan_rejects_invalid_estimation_and_unpaired_suspension():
    invalid = base_plan()
    invalid["estimation"] = {"method": "guess", "planned_effort_hours": 10}
    with pytest.raises(ValidationError):
        PlanCreate(**invalid)
    invalid = base_plan()
    invalid["resumption_criteria"] = []
    with pytest.raises(ValidationError):
        PlanCreate(**invalid)


def test_plan_baseline_hash_ignores_runtime_metadata_and_detects_scope_change():
    plan = {**base_plan(), "strategy_id": "TSTR-LINEAGE", "strategy_version": 2, "strategy_snapshot_hash": "abc", "revision": 1}
    first = plan_snapshot_hash(plan)
    plan["revision"] = 99
    plan["updated_at"] = "later"
    assert plan_snapshot_hash(plan) == first
    plan["quality_targets"] = [{"key": "pass_rate", "operator": ">=", "value": 0.99}]
    assert plan_snapshot_hash(plan) != first
