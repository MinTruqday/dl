from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from src.domain.contracts.common import (
    KnowledgeApprovalStatus,
    KnowledgeAuthority,
    KnowledgeSourceType,
    empty_doc,
)

class AcceptanceCriterionInput(BaseModel):
    key: str = Field(min_length=1, max_length=80)
    content_doc: dict[str, Any] = Field(default_factory=empty_doc)
    status: Literal["draft", "approved", "obsolete"] = "draft"
    source_span: dict[str, Any] | None = None


class RequirementCreate(BaseModel):
    requirement_key: str | None = Field(default=None, max_length=80)
    title: str = Field(min_length=2, max_length=300)
    type: Literal[
        "functional",
        "non_functional",
        "business_rule",
        "api",
        "ui",
        "data",
        "permission",
        "integration",
        "constraint",
    ] = "functional"
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    risk: Literal["critical", "high", "medium", "low"] = "medium"
    content_doc: dict[str, Any] = Field(default_factory=empty_doc)
    acceptance_criteria: list[AcceptanceCriterionInput] = Field(
        default_factory=list, max_length=200
    )
    business_rules: list[str] = Field(default_factory=list, max_length=200)
    actors: list[str] = Field(default_factory=list, max_length=100)
    dependencies: list[str] = Field(default_factory=list, max_length=200)
    source_refs: list[dict[str, Any]] = Field(default_factory=list, max_length=200)
    tags: list[str] = Field(default_factory=list, max_length=100)
    owner_id: str | None = Field(default=None, max_length=200)


class RequirementDraftPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    requirement_key: str | None = Field(default=None, max_length=80)
    title: str | None = Field(default=None, min_length=2, max_length=300)
    type: str | None = None
    priority: str | None = None
    risk: str | None = None
    content_doc: dict[str, Any] | None = None
    acceptance_criteria: list[AcceptanceCriterionInput] | None = Field(default=None, max_length=200)
    business_rules: list[str] | None = Field(default=None, max_length=200)
    actors: list[str] | None = Field(default=None, max_length=100)
    dependencies: list[str] | None = Field(default=None, max_length=200)
    source_refs: list[dict[str, Any]] | None = Field(default=None, max_length=200)
    tags: list[str] | None = Field(default=None, max_length=100)
    owner_id: str | None = Field(default=None, max_length=200)


class RequirementAIAnalysisInput(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    instruction: str = Field(default="", max_length=5000)


class RequirementAISuggestionApply(BaseModel):
    expected_revision: int = Field(ge=1)
    ai_result_id: str = Field(min_length=1, max_length=200)
    suggestion_id: str = Field(min_length=1, max_length=200)


class RequirementVersionCreate(RequirementCreate):
    change_reason: str = Field(min_length=2, max_length=2000)
    expected_current_version_id: str


class RequirementBaselineInput(BaseModel):
    expected_revision: int = Field(ge=1)
    review_note: str = Field(default="", max_length=2000)


class RequirementObsoleteInput(BaseModel):
    expected_current_version_id: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=2, max_length=2000)


class RequirementRestoreInput(BaseModel):
    expected_current_version_id: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=2, max_length=2000)


class ReviewTransitionInput(BaseModel):
    expected_revision: int = Field(ge=1)
    review_note: str = Field(default="", max_length=2000)


class RequirementCompareInput(BaseModel):
    from_version_id: str
    to_version_id: str


class RequirementDependencyInput(BaseModel):
    dependency_requirement_id: str = Field(min_length=1, max_length=200)
    expected_revision: int = Field(ge=1)


class RequirementSplitInput(BaseModel):
    expected_source_version_id: str = Field(min_length=1, max_length=200)
    idempotency_key: str = Field(min_length=8, max_length=200)
    reason: str = Field(min_length=2, max_length=2000)
    drafts: list[RequirementCreate] = Field(min_length=2, max_length=20)


class RequirementMergeInput(BaseModel):
    source_requirement_ids: list[str] = Field(min_length=2, max_length=20)
    expected_source_version_ids: dict[str, str] = Field(min_length=2, max_length=20)
    idempotency_key: str = Field(min_length=8, max_length=200)
    reason: str = Field(min_length=2, max_length=2000)
    draft: RequirementCreate


class RequirementDuplicateCheckInput(BaseModel):
    requirement_ids: list[str] = Field(default_factory=list, max_length=500)
    threshold: float = Field(default=0.72, ge=0.3, le=1)
    limit: int = Field(default=100, ge=1, le=1000)


class ImportCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=300)
    format: Literal["pdf", "docx", "md", "txt", "csv", "xlsx", "openapi", "postman"]
    content: str | dict[str, Any] | list[Any]


class RequirementExtractionInput(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)


class RequirementParseRetry(BaseModel):
    expected_revision: int = Field(ge=1)


class RequirementDocumentPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=2, max_length=300)
    source_type: KnowledgeSourceType | None = None
    authority: KnowledgeAuthority | None = None
    owner_id: str | None = Field(default=None, max_length=200)
    module: str | None = Field(default=None, max_length=200)
    component: str | None = Field(default=None, max_length=200)
    product_area: str | None = Field(default=None, max_length=200)
    release_id: str | None = Field(default=None, max_length=200)
    external_source_id: str | None = Field(default=None, max_length=500)
    approval_status: KnowledgeApprovalStatus | None = None
    approved_by: str | None = Field(default=None, max_length=200)
    approved_at: datetime | None = None
    source_version: str | None = Field(default=None, max_length=100)
    effective_from: datetime | None = None
    tags: list[str] | None = Field(default=None, max_length=100)


class KnowledgeSourceCreate(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    content: str = Field(min_length=1, max_length=2_000_000)
    source_type: KnowledgeSourceType = "REFERENCE"
    authority: KnowledgeAuthority = "PROJECT_REFERENCE"
    source_url: str | None = Field(default=None, max_length=2000)
    owner_id: str | None = Field(default=None, max_length=200)
    module: str | None = Field(default=None, max_length=200)
    component: str | None = Field(default=None, max_length=200)
    product_area: str | None = Field(default=None, max_length=200)
    release_id: str | None = Field(default=None, max_length=200)
    external_source_id: str | None = Field(default=None, max_length=500)
    approval_status: KnowledgeApprovalStatus = "DRAFT"
    approved_by: str | None = Field(default=None, max_length=200)
    approved_at: datetime | None = None
    source_version: str = Field(default="1", min_length=1, max_length=100)
    effective_from: datetime | None = None
    tags: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_approval(self):
        if self.approval_status == "APPROVED" and (not self.approved_by or not self.approved_at):
            raise ValueError("Nguồn đã phê duyệt phải có người và thời điểm phê duyệt")
        return self


class AttachmentCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=2000)
    item_id: str | None = Field(default=None, max_length=200)
    size: int = Field(default=0, ge=0)
    content_type: str = Field(default="application/octet-stream", max_length=200)
    artifact_type: str | None = Field(default=None, max_length=80)
    artifact_id: str | None = Field(default=None, max_length=200)


class AttachmentModeration(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)


class ReviewCommentCreate(BaseModel):
    artifact_type: str = Field(min_length=1, max_length=80)
    artifact_id: str = Field(min_length=1, max_length=200)
    body_doc: dict[str, Any] = Field(default_factory=empty_doc)
    anchor: dict[str, Any] | None = None
    parent_comment_id: str | None = None


class ReviewCommentAction(BaseModel):
    reason: str = Field(default="", max_length=2000)


class ReviewCommentPatch(BaseModel):
    body_doc: dict[str, Any]

    @field_validator("body_doc")
    @classmethod
    def validate_body(cls, value):
        if value.get("type") != "doc" or not isinstance(value.get("content", []), list):
            raise ValueError("Tiptap JSON không hợp lệ")
        return value


class ImportConfirm(BaseModel):
    selected_indexes: list[int] = Field(default_factory=list, max_length=2000)
    expected_revision: int | None = Field(default=None, ge=1)


class APIArtifactReview(BaseModel):
    expected_revision: int = Field(ge=1)
    selected_indexes: list[int] = Field(default_factory=list, max_length=5000)
    review_note: str = Field(default="", max_length=2000)


class APIArtifactConfirm(BaseModel):
    expected_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)


class APIArtifactArchive(BaseModel):
    expected_revision: int = Field(ge=1)
    reason: str = Field(min_length=2, max_length=2000)


class APIArtifactImpact(BaseModel):
    from_artifact_id: str = Field(min_length=1, max_length=200)
    to_artifact_id: str = Field(min_length=1, max_length=200)


class RequirementCandidateReview(RequirementCreate):
    candidate_id: str | None = Field(default=None, max_length=200)
    candidate_status: Literal["ACTIVE", "REJECTED", "SUPERSEDED"] = "ACTIVE"
    candidate_revision: int = Field(default=1, ge=1)
    extraction_confidence: float = Field(default=1, ge=0, le=1)
    candidate_relation: str | None = Field(default=None, max_length=80)
    parent_candidate_ids: list[str] = Field(default_factory=list, max_length=500)


class RequirementImportReview(BaseModel):
    expected_revision: int = Field(ge=1)
    preview: list[RequirementCandidateReview] = Field(min_length=1, max_length=500)
    review_note: str = Field(default="", max_length=2000)


class RequirementCandidateMergeInput(BaseModel):
    expected_revision: int = Field(ge=1)
    candidate_ids: list[str] = Field(min_length=2, max_length=500)
    merged: RequirementCreate
    reason: str = Field(default="", max_length=2000)


class RequirementCandidateSplitInput(BaseModel):
    expected_revision: int = Field(ge=1)
    drafts: list[RequirementCreate] = Field(min_length=2, max_length=100)
    reason: str = Field(default="", max_length=2000)


class RequirementCandidateRejectInput(BaseModel):
    expected_revision: int = Field(ge=1)
    reason: str = Field(default="", max_length=2000)

