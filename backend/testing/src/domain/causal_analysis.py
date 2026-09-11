from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class CausalAnalysisCreate(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)
    defect_ids: list[str] = Field(min_length=1, max_length=500)
    problem_statement: str = Field(min_length=2, max_length=10000)
    evidence: list[dict[str, Any] | str] = Field(min_length=1, max_length=1000)
    root_causes: list[dict[str, Any] | str] = Field(default_factory=list, max_length=200)
    contributing_factors: list[dict[str, Any] | str] = Field(default_factory=list, max_length=500)
    five_whys: list[str] = Field(default_factory=list, max_length=5)
    owner_id: str = Field(min_length=1, max_length=200)
    effectiveness_review_at: datetime | None = None


class CausalAnalysisPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    problem_statement: str | None = Field(default=None, min_length=2, max_length=10000)
    evidence: list[dict[str, Any] | str] | None = Field(default=None, min_length=1, max_length=1000)
    root_causes: list[dict[str, Any] | str] | None = Field(default=None, max_length=200)
    contributing_factors: list[dict[str, Any] | str] | None = Field(default=None, max_length=500)
    five_whys: list[str] | None = Field(default=None, max_length=5)
    owner_id: str | None = Field(default=None, min_length=1, max_length=200)
    effectiveness_review_at: datetime | None = None


class PreventionActionCreate(BaseModel):
    action_type: Literal["CORRECTIVE", "PREVENTIVE"]
    title: str = Field(min_length=2, max_length=500)
    description: str = Field(min_length=2, max_length=5000)
    owner_id: str = Field(min_length=1, max_length=200)
    due_at: datetime
    evidence_refs: list[str] = Field(default_factory=list, max_length=500)


class PreventionActionPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    status: Literal["OPEN", "IN_PROGRESS", "IMPLEMENTED", "EFFECTIVENESS_REVIEW", "CLOSED"]
    result: str = Field(default="", max_length=5000)
    evidence_refs: list[str] | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_result(self):
        if self.status in {"IMPLEMENTED", "EFFECTIVENESS_REVIEW", "CLOSED"} and not self.result.strip():
            raise ValueError("Hành động đã triển khai phải có kết quả")
        return self


class CausalTransition(BaseModel):
    expected_revision: int = Field(ge=1)
    status: Literal["IN_PROGRESS", "IMPLEMENTED", "EFFECTIVENESS_REVIEW", "CLOSED"]
    note: str = Field(default="", max_length=5000)


class CausalApproval(BaseModel):
    expected_revision: int = Field(ge=1)
    decision: Literal["APPROVE", "REQUEST_CHANGES"]
    note: str = Field(default="", max_length=5000)


class CausalAiRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    instruction: str = Field(default="", max_length=5000)
