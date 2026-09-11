from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class NonFunctionalTestPlanCreate(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)
    plan_type: Literal["SECURITY_TEST_PLAN", "PERFORMANCE_TEST_PLAN"]
    name: str = Field(min_length=2, max_length=500)
    objective: str = Field(min_length=2, max_length=5000)
    scope: list[str] = Field(min_length=1, max_length=500)
    approach: str = Field(min_length=2, max_length=10000)
    entry_criteria: list[str] = Field(default_factory=list, max_length=200)
    exit_criteria: list[str] = Field(default_factory=list, max_length=200)
    test_condition_ids: list[str] = Field(default_factory=list, max_length=1000)
    test_case_version_ids: list[str] = Field(default_factory=list, max_length=5000)
    requirement_version_ids: list[str] = Field(default_factory=list, max_length=5000)
    source_ai_result_ids: list[str] = Field(default_factory=list, max_length=100)
    tools: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_trace(self):
        if not self.test_condition_ids and not self.test_case_version_ids:
            raise ValueError("Kế hoạch NFR phải truy vết tới TestCondition hoặc TestCase")
        return self


class NonFunctionalTestPlanPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=500)
    objective: str | None = Field(default=None, min_length=2, max_length=5000)
    scope: list[str] | None = Field(default=None, min_length=1, max_length=500)
    approach: str | None = Field(default=None, min_length=2, max_length=10000)
    entry_criteria: list[str] | None = Field(default=None, max_length=200)
    exit_criteria: list[str] | None = Field(default=None, max_length=200)
    test_condition_ids: list[str] | None = Field(default=None, max_length=1000)
    test_case_version_ids: list[str] | None = Field(default=None, max_length=5000)
    requirement_version_ids: list[str] | None = Field(default=None, max_length=5000)
    tools: list[str] | None = Field(default=None, max_length=100)


class NonFunctionalTransition(BaseModel):
    expected_revision: int = Field(ge=1)
    note: str = Field(default="", max_length=5000)


class ExternalTestEvidenceImport(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    provider: Literal["GENERIC", "K6", "JMETER", "OWASP_ZAP", "PLAYWRIGHT"] = "GENERIC"
    external_run_ref: str = Field(min_length=1, max_length=500)
    executed_at: datetime
    evidence_refs: list[str] = Field(min_length=1, max_length=1000)
    result_summary: dict[str, Any] = Field(min_length=1, max_length=500)
    raw_result_hash: str = Field(min_length=32, max_length=128)

    @model_validator(mode="after")
    def validate_executed_at(self):
        if self.executed_at.tzinfo is None:
            raise ValueError("Thời điểm thực thi phải có múi giờ")
        return self
