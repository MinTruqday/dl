import hashlib
import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


StrategyStatus = Literal["DRAFT", "IN_REVIEW", "APPROVED", "SUPERSEDED", "ARCHIVED"]


class RiskModel(BaseModel):
    probability_scale: list[dict[str, Any]] = Field(min_length=1, max_length=20)
    impact_scale: list[dict[str, Any]] = Field(min_length=1, max_length=20)
    risk_exposure_formula: str = Field(min_length=1, max_length=1000)
    thresholds: list[dict[str, Any]] = Field(min_length=1, max_length=50)
    mandatory_test_depth: dict[str, Any] = Field(default_factory=dict)
    regression_priority_rules: list[str] = Field(default_factory=list, max_length=100)


class TestStrategyFields(BaseModel):
    name: str = Field(min_length=2, max_length=300)
    objective: str = Field(min_length=2, max_length=5000)
    test_levels: list[str] = Field(min_length=1, max_length=20)
    test_types: list[str] = Field(min_length=1, max_length=100)
    approach: str = Field(min_length=2, max_length=10000)
    risk_model: RiskModel
    technique_policy: dict[str, Any] = Field(default_factory=dict)
    automation_policy: dict[str, Any] = Field(default_factory=dict)
    environment_policy: dict[str, Any] = Field(default_factory=dict)
    test_data_policy: dict[str, Any] = Field(default_factory=dict)
    defect_policy: dict[str, Any] = Field(default_factory=dict)
    review_policy: dict[str, Any] = Field(default_factory=dict)
    entry_criteria_defaults: list[str] = Field(default_factory=list, max_length=200)
    exit_criteria_defaults: list[str] = Field(default_factory=list, max_length=200)
    suspension_criteria: list[str] = Field(default_factory=list, max_length=200)
    resumption_criteria: list[str] = Field(default_factory=list, max_length=200)
    deliverables: list[str] = Field(default_factory=list, max_length=200)
    reporting_policy: dict[str, Any] = Field(default_factory=dict)
    quality_objectives: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    standards_refs: list[str] = Field(default_factory=list, max_length=100)
    tailoring_rationale: str = Field(default="", max_length=5000)
    reviewer_ids: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_suspension_pairs(self):
        if bool(self.suspension_criteria) != bool(self.resumption_criteria):
            raise ValueError("Tiêu chí đình chỉ và tiếp tục phải được khai báo cùng nhau")
        return self


class TestStrategyCreate(TestStrategyFields):
    key: str = Field(min_length=2, max_length=80, pattern=r"^[A-Z][A-Z0-9_-]+$")


class TestStrategyPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=300)
    objective: str | None = Field(default=None, min_length=2, max_length=5000)
    test_levels: list[str] | None = Field(default=None, min_length=1, max_length=20)
    test_types: list[str] | None = Field(default=None, min_length=1, max_length=100)
    approach: str | None = Field(default=None, min_length=2, max_length=10000)
    risk_model: RiskModel | None = None
    technique_policy: dict[str, Any] | None = None
    automation_policy: dict[str, Any] | None = None
    environment_policy: dict[str, Any] | None = None
    test_data_policy: dict[str, Any] | None = None
    defect_policy: dict[str, Any] | None = None
    review_policy: dict[str, Any] | None = None
    entry_criteria_defaults: list[str] | None = Field(default=None, max_length=200)
    exit_criteria_defaults: list[str] | None = Field(default=None, max_length=200)
    suspension_criteria: list[str] | None = Field(default=None, max_length=200)
    resumption_criteria: list[str] | None = Field(default=None, max_length=200)
    deliverables: list[str] | None = Field(default=None, max_length=200)
    reporting_policy: dict[str, Any] | None = None
    quality_objectives: list[dict[str, Any]] | None = Field(default=None, max_length=100)
    standards_refs: list[str] | None = Field(default=None, max_length=100)
    tailoring_rationale: str | None = Field(default=None, max_length=5000)
    reviewer_ids: list[str] | None = Field(default=None, max_length=100)


class StrategyTransitionInput(BaseModel):
    expected_revision: int = Field(ge=1)
    note: str = Field(default="", max_length=5000)


class StrategyVersionInput(BaseModel):
    expected_revision: int = Field(ge=1)
    change_reason: str = Field(min_length=2, max_length=5000)


def strategy_snapshot(strategy):
    fields = tuple(TestStrategyFields.model_fields)
    return {
        "strategy_id": strategy["_id"],
        "lineage_id": strategy["lineage_id"],
        "project_id": strategy["project_id"],
        "key": strategy["key"],
        "version": strategy["version"],
        **{field: strategy.get(field) for field in fields},
    }


def strategy_hash(strategy):
    value = json.dumps(strategy_snapshot(strategy), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def iso_value(value):
    return value.isoformat() if isinstance(value, datetime) else value
