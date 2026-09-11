from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.core.auth import ProjectRole, permissions_for_role
from src.domain.test_strategy import TestStrategyCreate as StrategyCreate
from src.domain.test_strategy import TestStrategyFields as StrategyFields
from src.domain.test_strategy import strategy_hash, strategy_snapshot


def strategy_payload():
    return {
        "key": "STR_LOGIN",
        "name": "Chiến lược kiểm thử đăng nhập",
        "objective": "Xác nhận tính đúng đắn và an toàn của luồng đăng nhập",
        "test_levels": ["SYSTEM", "ACCEPTANCE"],
        "test_types": ["FUNCTIONAL", "SECURITY"],
        "approach": "Kiểm thử dựa trên rủi ro và truy vết yêu cầu",
        "risk_model": {
            "probability_scale": [{"value": 1, "label": "Thấp"}, {"value": 2, "label": "Cao"}],
            "impact_scale": [{"value": 1, "label": "Thấp"}, {"value": 2, "label": "Cao"}],
            "risk_exposure_formula": "probability * impact",
            "thresholds": [{"level": "HIGH", "min": 3}],
            "mandatory_test_depth": {"HIGH": "FULL"},
            "regression_priority_rules": ["HIGH trước MEDIUM"],
        },
        "entry_criteria_defaults": ["Yêu cầu đã baseline"],
        "exit_criteria_defaults": ["Không còn lỗi blocker"],
        "suspension_criteria": ["Môi trường không khả dụng"],
        "resumption_criteria": ["Môi trường đã được xác minh"],
        "reviewer_ids": ["TESTER-1"],
    }


def test_strategy_schema_requires_explainable_risk_model():
    value = StrategyCreate(**strategy_payload())
    assert value.risk_model.risk_exposure_formula == "probability * impact"
    invalid = strategy_payload()
    invalid["risk_model"] = {**invalid["risk_model"], "thresholds": []}
    with pytest.raises(ValidationError):
        StrategyCreate(**invalid)


def test_strategy_requires_suspension_and_resumption_as_pair():
    invalid = strategy_payload()
    invalid["resumption_criteria"] = []
    with pytest.raises(ValidationError):
        StrategyCreate(**invalid)


def test_strategy_snapshot_hash_is_stable_and_content_sensitive():
    payload = strategy_payload()
    payload.pop("key")
    strategy = {
        "_id": "TSTR-1",
        "lineage_id": "TSTR-1",
        "project_id": "PROJECT-1",
        "key": "STR_LOGIN",
        "version": 1,
        **StrategyFields(**payload).model_dump(),
        "created_at": datetime.now(timezone.utc),
    }
    first = strategy_hash(strategy)
    strategy["updated_at"] = datetime.now(timezone.utc)
    assert strategy_hash(strategy) == first
    strategy["approach"] = "Cách tiếp cận đã thay đổi"
    assert strategy_hash(strategy) != first
    assert strategy_snapshot(strategy)["version"] == 1


def test_strategy_permissions_cover_all_project_roles():
    lead = permissions_for_role(ProjectRole.QA_LEAD)
    tester = permissions_for_role(ProjectRole.TESTER)
    analyst = permissions_for_role(ProjectRole.BA)
    developer = permissions_for_role(ProjectRole.DEVELOPER)
    viewer = permissions_for_role(ProjectRole.VIEWER)
    assert {
        "teststrategy.read",
        "teststrategy.create",
        "teststrategy.update",
        "teststrategy.submit_review",
        "teststrategy.review",
        "teststrategy.approve",
        "teststrategy.version.read",
        "teststrategy.archive",
    } <= lead
    assert {"teststrategy.read", "teststrategy.create", "teststrategy.update", "teststrategy.submit_review", "teststrategy.review", "teststrategy.version.read"} <= tester
    assert {"teststrategy.read", "teststrategy.review", "teststrategy.version.read"} <= analyst
    assert {"teststrategy.read", "teststrategy.version.read"} <= developer
    assert {"teststrategy.read", "teststrategy.version.read"} <= viewer
    assert "teststrategy.approve" not in tester | analyst | developer | viewer
