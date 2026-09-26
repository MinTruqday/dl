from datetime import datetime
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, Field, model_validator


class QualityEvaluationCreate(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)
    release_id: str = Field(min_length=1, max_length=200)
    build_id: str = Field(min_length=1, max_length=200)
    measurement_snapshot_refs: list[str] = Field(default_factory=list, max_length=500)
    monitoring_snapshot_id: str = Field(min_length=1, max_length=200)
    critical_risks: list[dict[str, Any] | str] = Field(default_factory=list, max_length=500)
    evidence_refs: list[str] = Field(default_factory=list, max_length=1000)
    recommendation: (
        Literal["GO", "GO_WITH_RISK", "NO_GO", "MORE_TESTING_REQUIRED", "INSUFFICIENT_DATA"] | None
    ) = None
    rationale: str = Field(min_length=2, max_length=10000)


class QualityEvaluationPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    critical_risks: list[dict[str, Any] | str] | None = Field(default=None, max_length=500)
    evidence_refs: list[str] | None = Field(default=None, max_length=1000)
    recommendation: (
        Literal["GO", "GO_WITH_RISK", "NO_GO", "MORE_TESTING_REQUIRED", "INSUFFICIENT_DATA"] | None
    ) = None
    rationale: str | None = Field(default=None, min_length=2, max_length=10000)


class QualityEvaluationTransition(BaseModel):
    expected_revision: int = Field(ge=1)
    note: str = Field(default="", max_length=5000)


class QualityEvaluationReview(BaseModel):
    expected_revision: int = Field(ge=1)
    decision: Literal["ENDORSE", "REQUEST_CHANGES"]
    note: str = Field(default="", max_length=5000)


class QualityWaiverCreate(BaseModel):
    expected_revision: int | None = Field(default=None, ge=1)
    criterion_or_metric: str = Field(
        min_length=1,
        max_length=500,
        validation_alias=AliasChoices("criterion_or_metric", "metric_or_criterion"),
    )
    actual: Any = None
    threshold: Any = None
    reason: str = Field(min_length=2, max_length=5000)
    risk: str = Field(min_length=2, max_length=5000)
    owner_id: str = Field(min_length=1, max_length=200)
    expiry_at: datetime = Field(validation_alias=AliasChoices("expiry_at", "expiry"))
    evidence_refs: list[str] = Field(
        min_length=1, max_length=500, validation_alias=AliasChoices("evidence_refs", "evidence")
    )

    @model_validator(mode="after")
    def validate_expiry(self):
        if self.expiry_at.tzinfo is None:
            raise ValueError("Thời hạn waiver phải có múi giờ")
        return self


class QualityWaiverDecision(BaseModel):
    expected_revision: int = Field(ge=1)
    decision: Literal["APPROVE", "REJECT"]
    note: str = Field(default="", max_length=5000)

    @model_validator(mode="after")
    def validate_rejection(self):
        if self.decision == "REJECT" and not self.note.strip():
            raise ValueError("Từ chối waiver phải có lý do")
        return self
