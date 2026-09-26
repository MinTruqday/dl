from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ProcessImprovementCreate(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)
    source: Literal["LESSON_LEARNED", "RCA", "MEASUREMENT", "REVIEW", "MANUAL"]
    source_refs: list[str] = Field(default_factory=list, max_length=500)
    observed_problem: str = Field(min_length=2, max_length=10000)
    evidence_refs: list[str] = Field(min_length=1, max_length=1000)
    proposed_change: str = Field(min_length=2, max_length=10000)
    expected_effect: str = Field(min_length=2, max_length=10000)
    experiment_scope: str = Field(min_length=2, max_length=10000)
    owner_id: str = Field(min_length=1, max_length=200)


class ProcessImprovementPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    observed_problem: str | None = Field(default=None, min_length=2, max_length=10000)
    evidence_refs: list[str] | None = Field(default=None, min_length=1, max_length=1000)
    proposed_change: str | None = Field(default=None, min_length=2, max_length=10000)
    expected_effect: str | None = Field(default=None, min_length=2, max_length=10000)
    experiment_scope: str | None = Field(default=None, min_length=2, max_length=10000)
    owner_id: str | None = Field(default=None, min_length=1, max_length=200)


class ProcessImprovementLink(BaseModel):
    expected_revision: int = Field(ge=1)
    lesson_refs: list[str] = Field(default_factory=list, max_length=500)
    causal_analysis_refs: list[str] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def require_reference(self):
        if not self.lesson_refs and not self.causal_analysis_refs:
            raise ValueError("Phải chọn ít nhất một bài học hoặc RCA")
        return self


class ProcessImprovementTransition(BaseModel):
    expected_revision: int = Field(ge=1)
    note: str = Field(default="", max_length=5000)


class ProcessImprovementMetrics(BaseModel):
    expected_revision: int = Field(ge=1)
    measurement_snapshot_refs: list[str] = Field(min_length=1, max_length=1000)
    note: str = Field(default="", max_length=5000)


class ProcessImprovementEvaluation(ProcessImprovementMetrics):
    decision: Literal["ADOPT", "REJECT"]
    conclusion: str = Field(min_length=2, max_length=10000)


class StatisticalBaselineCreate(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)
    measurement_definition_id: str = Field(min_length=1, max_length=200)
    measurement_snapshot_refs: list[str] = Field(min_length=5, max_length=1000)
    baseline_label: str = Field(min_length=2, max_length=300)

    @model_validator(mode="after")
    def require_distinct_snapshots(self):
        if len(set(self.measurement_snapshot_refs)) != len(self.measurement_snapshot_refs):
            raise ValueError("Ảnh đo lường trong cửa sổ cơ sở phải duy nhất")
        return self


class StatisticalSpecialCause(BaseModel):
    expected_revision: int = Field(ge=1)
    measurement_snapshot_id: str = Field(min_length=1, max_length=200)
    cause: str = Field(min_length=2, max_length=5000)
    evidence_refs: list[str] = Field(min_length=1, max_length=500)


class StatisticalComparison(BaseModel):
    before_analysis_id: str = Field(min_length=1, max_length=200)
    after_analysis_id: str = Field(min_length=1, max_length=200)
    process_improvement_id: str | None = Field(default=None, max_length=200)


class StatisticalPoint(BaseModel):
    snapshot_id: str
    value: float
    measured_at: Any = None
