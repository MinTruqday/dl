from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


ReviewType = Literal["REQUIREMENT_REVIEW", "TEST_STRATEGY_REVIEW", "TEST_PLAN_REVIEW", "TEST_CONDITION_REVIEW", "TEST_CASE_REVIEW", "IMPACT_REVIEW", "COMPLETION_REVIEW"]
FindingSeverity = Literal["MAJOR", "MINOR", "QUESTION", "IMPROVEMENT"]
FindingCategory = Literal["CORRECTNESS", "COMPLETENESS", "CONSISTENCY", "TESTABILITY", "TRACEABILITY", "SECURITY", "PERFORMANCE", "MAINTAINABILITY"]


class ReviewSessionCreate(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)
    review_type: ReviewType
    artifact_type: str = Field(min_length=2, max_length=100)
    artifact_id: str = Field(min_length=1, max_length=200)
    artifact_version_id: str = Field(min_length=1, max_length=200)
    objective: str = Field(min_length=2, max_length=5000)
    checklist_version: str = Field(min_length=1, max_length=100)
    moderator_id: str = Field(min_length=1, max_length=200)
    author_id: str = Field(min_length=1, max_length=200)
    reviewers: list[str] = Field(min_length=1, max_length=100)
    scribe_id: str | None = Field(default=None, max_length=200)
    planned_at: datetime | None = None
    checklist: list[dict[str, Any]] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def validate_participants(self):
        self.reviewers = list(dict.fromkeys(self.reviewers))
        if self.moderator_id in self.reviewers or self.author_id in self.reviewers:
            raise ValueError("Moderator và tác giả không đồng thời là reviewer")
        return self


class ReviewSessionPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    objective: str | None = Field(default=None, min_length=2, max_length=5000)
    checklist_version: str | None = Field(default=None, min_length=1, max_length=100)
    moderator_id: str | None = Field(default=None, min_length=1, max_length=200)
    reviewers: list[str] | None = Field(default=None, min_length=1, max_length=100)
    scribe_id: str | None = Field(default=None, max_length=200)
    planned_at: datetime | None = None
    checklist: list[dict[str, Any]] | None = Field(default=None, max_length=200)


class ReviewFindingCreate(BaseModel):
    category: FindingCategory
    severity: FindingSeverity
    anchor: dict[str, Any] = Field(default_factory=dict)
    description: str = Field(min_length=2, max_length=5000)
    suggested_action: str = Field(default="", max_length=5000)
    owner_id: str = Field(min_length=1, max_length=200)


class ReviewFindingPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    status: Literal["OPEN", "IN_PROGRESS", "RESOLVED", "ACCEPTED"]
    resolution: str = Field(default="", max_length=5000)

    @model_validator(mode="after")
    def validate_resolution(self):
        if self.status in {"RESOLVED", "ACCEPTED"} and not self.resolution.strip():
            raise ValueError("Finding đã xử lý phải có kết quả")
        return self


class ReviewTransition(BaseModel):
    expected_revision: int = Field(ge=1)
    note: str = Field(default="", max_length=5000)
    decision: Literal["ACCEPTED", "ACCEPTED_WITH_ACTIONS", "REWORK_REQUIRED", "REJECTED"] | None = None
