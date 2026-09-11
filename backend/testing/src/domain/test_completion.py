import hashlib
import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


CompletionRecommendation = Literal["READY_FOR_RELEASE", "READY_WITH_RISK", "NOT_READY", "CONTINUE_TESTING"]


class ResidualRisk(BaseModel):
    risk_id: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=2, max_length=500)
    description: str = Field(default="", max_length=5000)
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    owner_id: str = Field(min_length=1, max_length=200)
    acceptance: Literal["PENDING", "ACCEPTED", "MITIGATE", "TRANSFER", "AVOID"] = "PENDING"
    acceptance_reason: str = Field(default="", max_length=5000)
    accepted_by: str | None = Field(default=None, max_length=200)
    accepted_at: datetime | None = None

    @model_validator(mode="after")
    def validate_acceptance(self):
        if self.acceptance != "PENDING" and (not self.acceptance_reason.strip() or not self.accepted_by):
            raise ValueError("Residual risk đã xử lý phải có lý do và người chấp nhận")
        return self


class ImprovementAction(BaseModel):
    action_id: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=2, max_length=500)
    owner_id: str = Field(min_length=1, max_length=200)
    due_at: datetime | None = None
    status: Literal["OPEN", "IN_PROGRESS", "DONE", "CANCELLED"] = "OPEN"
    evidence_refs: list[str] = Field(default_factory=list, max_length=500)


class TestCompletionCreate(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)
    snapshot_id: str = Field(min_length=1, max_length=200)
    build_id: str = Field(min_length=1, max_length=200)
    unresolved_items: list[dict[str, Any] | str] = Field(default_factory=list, max_length=1000)
    residual_risks: list[ResidualRisk] = Field(default_factory=list, max_length=500)
    deviations: list[dict[str, Any] | str] = Field(default_factory=list, max_length=500)
    testware_handover: list[dict[str, Any] | str] = Field(default_factory=list, max_length=1000)
    archived_artifacts: list[dict[str, Any] | str] = Field(default_factory=list, max_length=1000)
    environment_closure: list[dict[str, Any] | str] = Field(default_factory=list, max_length=500)
    lessons_learned: list[dict[str, Any] | str] = Field(default_factory=list, max_length=500)
    improvement_actions: list[ImprovementAction] = Field(default_factory=list, max_length=500)
    recommendation: CompletionRecommendation | None = None


class TestCompletionPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    execution_summary: dict[str, Any] | None = None
    coverage_summary: dict[str, Any] | None = None
    defect_summary: dict[str, Any] | None = None
    unresolved_items: list[dict[str, Any] | str] | None = Field(default=None, max_length=1000)
    residual_risks: list[ResidualRisk] | None = Field(default=None, max_length=500)
    deviations: list[dict[str, Any] | str] | None = Field(default=None, max_length=500)
    testware_handover: list[dict[str, Any] | str] | None = Field(default=None, max_length=1000)
    archived_artifacts: list[dict[str, Any] | str] | None = Field(default=None, max_length=1000)
    environment_closure: list[dict[str, Any] | str] | None = Field(default=None, max_length=500)
    lessons_learned: list[dict[str, Any] | str] | None = Field(default=None, max_length=500)
    improvement_actions: list[ImprovementAction] | None = Field(default=None, max_length=500)
    recommendation: CompletionRecommendation | None = None
    executive_summary: str | None = Field(default=None, max_length=10000)
    closure_summary: str | None = Field(default=None, max_length=10000)
    residual_risk_summary: str | None = Field(default=None, max_length=10000)
    recommendation_rationale: str | None = Field(default=None, max_length=10000)


class CompletionTransition(BaseModel):
    expected_revision: int = Field(ge=1)
    note: str = Field(default="", max_length=5000)


class CompletionSignOff(BaseModel):
    expected_revision: int = Field(ge=1)
    decision: Literal["APPROVE", "REJECT"]
    note: str = Field(default="", max_length=5000)


class ResidualRiskDecision(BaseModel):
    expected_revision: int = Field(ge=1)
    acceptance: Literal["ACCEPTED", "MITIGATE", "TRANSFER", "AVOID"]
    reason: str = Field(min_length=2, max_length=5000)


class TestCompletionAiDraft(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    instruction: str = Field(default="", max_length=5000)


def completion_snapshot(report):
    excluded = {
        "status", "revision", "created_by", "created_at", "updated_at", "submitted_by", "submitted_at",
        "reviewed_by", "reviewed_at", "approved_by", "approved_at", "closed_by", "closed_at",
        "approval_history", "review_history", "approved_snapshot", "approved_snapshot_hash", "change_request",
    }
    return {key: value for key, value in report.items() if key not in excluded}


def completion_hash(report):
    canonical = json.dumps(completion_snapshot(report), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
