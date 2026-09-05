from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


def empty_doc():
    return {"type": "doc", "content": []}


class ProjectCreate(BaseModel):
    key: str = Field(min_length=2, max_length=30, pattern=r"^[A-Z][A-Z0-9_-]+$")
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=5000)
    project_type: Literal["web", "mobile", "api", "desktop", "embedded", "other"] = "web"
    locale: str = Field(default="vi-VN", min_length=2, max_length=20)
    timezone: str = Field(default="Asia/Ho_Chi_Minh", min_length=2, max_length=80)
    settings: dict[str, Any] = Field(default_factory=dict)


class ProjectPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    project_type: Literal["web", "mobile", "api", "desktop", "embedded", "other"] | None = None
    locale: str | None = Field(default=None, min_length=2, max_length=20)
    timezone: str | None = Field(default=None, min_length=2, max_length=80)
    settings: dict[str, Any] | None = None


class ProjectArchiveInput(BaseModel):
    expected_revision: int = Field(ge=1)
    reason: str = Field(min_length=2, max_length=2000)


class ProjectMemberCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=200)
    project_role: Literal["QA_LEAD", "TESTER", "BA", "DEVELOPER", "VIEWER"]


class ProjectMemberPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    project_role: Literal["QA_LEAD", "TESTER", "BA", "DEVELOPER", "VIEWER"] | None = None
    status: Literal["ACTIVE", "INACTIVE"] | None = None


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
    acceptance_criteria: list[AcceptanceCriterionInput] = Field(default_factory=list, max_length=200)
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
    source_type: Literal["teacher_material", "official_textbook", "curriculum", "reference", "api_contract", "other"] | None = None
    authority: Literal["teacher", "official", "supplemental", "reference"] | None = None
    teacher_id: str | None = Field(default=None, max_length=200)
    subject: str | None = Field(default=None, max_length=200)
    grade: str | None = Field(default=None, max_length=100)
    tags: list[str] | None = Field(default=None, max_length=100)


class KnowledgeSourceCreate(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    content: str = Field(min_length=1, max_length=2_000_000)
    source_type: Literal[
        "teacher_material",
        "official_textbook",
        "curriculum",
        "reference",
        "api_contract",
        "other",
    ] = "reference"
    authority: Literal["teacher", "official", "supplemental", "reference"] = "reference"
    source_url: str | None = Field(default=None, max_length=2000)
    teacher_id: str | None = Field(default=None, max_length=200)
    subject: str | None = Field(default=None, max_length=200)
    grade: str | None = Field(default=None, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=100)


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


class ScenarioCreate(BaseModel):
    scenario_key: str | None = Field(default=None, max_length=80)
    title: str = Field(min_length=2, max_length=300)
    objective: str = Field(default="", max_length=5000)
    risk: Literal["critical", "high", "medium", "low"] = "medium"
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    requirement_version_ids: list[str] = Field(default_factory=list, max_length=200)
    acceptance_criterion_ids: list[str] = Field(default_factory=list, max_length=500)
    status: Literal["draft", "in_review", "approved", "archived"] = "draft"
    origin: Literal["manual", "ai_generated", "import"] = "manual"
    category: Literal[
        "happy_path",
        "negative",
        "boundary",
        "validation",
        "permission",
        "state_transition",
        "integration",
        "error_handling",
        "data_persistence",
        "concurrency",
    ] = "happy_path"


class ScenarioPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=2, max_length=300)
    objective: str | None = Field(default=None, max_length=5000)
    risk: str | None = None
    priority: str | None = None
    requirement_version_ids: list[str] | None = Field(default=None, max_length=200)
    acceptance_criterion_ids: list[str] | None = Field(default=None, max_length=500)
    category: str | None = None


class TestStep(BaseModel):
    id: str
    order: int = Field(ge=1)
    action_doc: dict[str, Any] = Field(default_factory=empty_doc)
    test_data: dict[str, Any] = Field(default_factory=dict)
    expected_doc: dict[str, Any] = Field(default_factory=empty_doc)


class TestCaseDraftCreate(BaseModel):
    test_case_key: str | None = Field(default=None, max_length=80)
    title: str = Field(min_length=2, max_length=300)
    type: Literal[
        "happy_path",
        "negative",
        "boundary",
        "validation",
        "permission",
        "state_transition",
        "integration",
        "error_handling",
        "data_persistence",
        "concurrency",
        "api",
        "ui",
        "custom",
    ] = "happy_path"
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    risk: Literal["critical", "high", "medium", "low"] = "medium"
    objective_doc: dict[str, Any] = Field(default_factory=empty_doc)
    preconditions_doc: dict[str, Any] = Field(default_factory=empty_doc)
    steps: list[TestStep] = Field(default_factory=list, max_length=500)
    test_data: dict[str, Any] = Field(default_factory=dict)
    expected_result_doc: dict[str, Any] = Field(default_factory=empty_doc)
    postconditions_doc: dict[str, Any] = Field(default_factory=empty_doc)
    tags: list[str] = Field(default_factory=list, max_length=100)
    owner_id: str | None = Field(default=None, max_length=200)
    techniques: list[str] = Field(default_factory=list, max_length=50)
    automation_status: Literal["manual", "candidate", "automated"] = "manual"
    attachments: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    data_set_version_ids: list[str] = Field(default_factory=list, max_length=100)
    requirement_version_ids: list[str] = Field(default_factory=list, max_length=200)
    acceptance_criterion_ids: list[str] = Field(default_factory=list, max_length=500)
    scenario_id: str | None = None
    origin: Literal["manual", "ai_generated", "clone", "import", "maintenance"] = "manual"
    source_evidence: list[dict[str, Any]] = Field(default_factory=list, max_length=200)

    @field_validator(
        "preconditions_doc",
        "objective_doc",
        "expected_result_doc",
        "postconditions_doc",
    )
    @classmethod
    def validate_documents(cls, value):
        if value.get("type") != "doc" or not isinstance(value.get("content", []), list):
            raise ValueError("Tiptap JSON không hợp lệ")
        return value

    @model_validator(mode="after")
    def validate_step_order(self):
        orders = [step.order for step in self.steps]
        if len(orders) != len(set(orders)):
            raise ValueError("Thứ tự bước kiểm thử không được trùng")
        return self


class TestCaseDraftPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=2, max_length=300)
    type: str | None = None
    priority: str | None = None
    risk: str | None = None
    objective_doc: dict[str, Any] | None = None
    preconditions_doc: dict[str, Any] | None = None
    steps: list[TestStep] | None = None
    test_data: dict[str, Any] | None = None
    expected_result_doc: dict[str, Any] | None = None
    postconditions_doc: dict[str, Any] | None = None
    tags: list[str] | None = None
    owner_id: str | None = Field(default=None, max_length=200)
    techniques: list[str] | None = None
    automation_status: str | None = None
    attachments: list[dict[str, Any]] | None = None
    data_set_version_ids: list[str] | None = None
    requirement_version_ids: list[str] | None = None
    acceptance_criterion_ids: list[str] | None = None
    scenario_id: str | None = None


class TestCaseFreezeInput(BaseModel):
    expected_revision: int = Field(ge=1)
    change_reason: str = Field(default="Phê duyệt phiên bản kiểm thử", max_length=2000)
    review_note: str = Field(default="", max_length=2000)


class TestCaseCloneInput(BaseModel):
    expected_current_version_id: str = Field(min_length=1, max_length=200)
    title: str | None = Field(default=None, min_length=2, max_length=300)


class DataSetCreate(BaseModel):
    name: str = Field(min_length=2, max_length=300)
    variables: dict[str, Any] = Field(default_factory=dict)
    secret_refs: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_secret_policy(self):
        sensitive_markers = ("password", "passwd", "token", "secret", "api_key", "private_key")
        unsafe_keys = [
            key for key in self.variables if any(marker in key.lower() for marker in sensitive_markers)
        ]
        if unsafe_keys:
            raise ValueError("Dữ liệu bí mật phải được khai báo bằng secret_refs")
        invalid_refs = [
            key for key, value in self.secret_refs.items() if not value.startswith("secret://")
        ]
        if invalid_refs:
            raise ValueError("Secret reference phải bắt đầu bằng secret://")
        return self


class DataSetVersionCreate(DataSetCreate):
    expected_current_version_id: str = Field(min_length=1, max_length=200)
    change_reason: str = Field(min_length=2, max_length=2000)


class DataSetBind(BaseModel):
    test_case_draft_id: str = Field(min_length=1, max_length=200)
    data_set_version_id: str = Field(min_length=1, max_length=200)
    expected_revision: int = Field(ge=1)


class DataSetPreview(BaseModel):
    data_set_version_id: str = Field(min_length=1, max_length=200)
    max_rows: int = Field(default=100, ge=1, le=1000)


class DataSetArchive(BaseModel):
    expected_revision: int = Field(ge=1)
    reason: str = Field(min_length=2, max_length=2000)


class RiskRankingGenerate(BaseModel):
    max_items: int | None = Field(default=None, ge=1, le=5000)


class RiskRankingPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    test_case_version_id: str = Field(min_length=1, max_length=200)
    included: bool
    reason: str = Field(min_length=2, max_length=2000)


class RiskRankingApproval(BaseModel):
    expected_revision: int = Field(ge=1)
    review_note: str = Field(default="", max_length=5000)


class TraceLinkCreate(BaseModel):
    project_id: str
    source_type: Literal["requirement_version", "acceptance_criterion", "test_scenario"]
    source_id: str
    target_type: Literal["test_case_version"] = "test_case_version"
    target_id: str
    link_type: Literal["verifies", "covers", "derived_from", "relates_to"] = "verifies"
    confidence: float = Field(default=1, ge=0, le=1)
    origin: Literal["manual", "ai_suggested", "import", "trace_recovery"] = "manual"
    evidence: list[dict[str, Any]] = Field(default_factory=list, max_length=200)


class ProposalAction(BaseModel):
    expected_revision: int = Field(ge=1)
    patch: dict[str, Any] | None = None
    review_note: str = Field(default="", max_length=2000)


class ProposalRegenerateInput(BaseModel):
    expected_revision: int = Field(ge=1)
    instruction: str = Field(min_length=2, max_length=5000)


class ImpactOverrideItem(BaseModel):
    test_case_version_id: str = Field(min_length=1, max_length=200)
    classification: Literal[
        "STILL_VALID",
        "POTENTIALLY_AFFECTED",
        "NEEDS_UPDATE",
        "OBSOLETE",
    ]
    reason: str = Field(min_length=2, max_length=2000)


class ImpactReviewInput(BaseModel):
    expected_revision: int = Field(ge=1)
    overrides: list[ImpactOverrideItem] = Field(default_factory=list, max_length=5000)
    review_note: str = Field(default="", max_length=5000)


class ImpactRerunInput(BaseModel):
    expected_revision: int = Field(ge=1)
    reason: str = Field(min_length=2, max_length=2000)
    knowledge_index_version: str | None = Field(default=None, max_length=200)
    algorithm_version: Literal["impact-pipeline-v1"] = "impact-pipeline-v1"


class ChangeSetReviewInput(BaseModel):
    expected_revision: int = Field(ge=1)
    changes: list[dict[str, Any]] = Field(min_length=1, max_length=500)
    review_note: str = Field(default="", max_length=5000)

    @field_validator("changes")
    @classmethod
    def validate_change_facts(cls, values):
        for value in values:
            if not str(value.get("type") or "").strip():
                raise ValueError("ChangeFact phải có type")
        return values


class RegressionApprovalInput(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=300)
    selected_test_case_version_ids: list[str] | None = Field(default=None, max_length=5000)
    review_note: str = Field(default="", max_length=5000)


class TestPlanCreate(BaseModel):
    project_id: str
    name: str = Field(min_length=2, max_length=300)
    objective: str = Field(default="", max_length=5000)
    scope_in: list[str] = Field(default_factory=list, max_length=500)
    scope_out: list[str] = Field(default_factory=list, max_length=500)
    environment: str = Field(default="staging", max_length=200)
    environment_id: str | None = Field(default=None, max_length=200)
    entry_criteria: list[str] = Field(default_factory=list, max_length=200)
    exit_criteria: list[str] = Field(default_factory=list, max_length=200)
    risks: list[str] = Field(default_factory=list, max_length=200)
    test_types: list[str] = Field(default_factory=list, max_length=100)
    members: list[str] = Field(default_factory=list, max_length=500)
    release: str = Field(default="", max_length=200)
    release_id: str | None = Field(default=None, max_length=200)
    build: str = Field(default="", max_length=200)
    build_id: str | None = Field(default=None, max_length=200)


class ReleaseCreate(BaseModel):
    key: str = Field(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]+$")
    name: str = Field(min_length=2, max_length=300)
    version: str = Field(min_length=1, max_length=120)
    notes: str = Field(default="", max_length=5000)
    planned_start_at: str | None = Field(default=None, max_length=80)
    planned_end_at: str | None = Field(default=None, max_length=80)
    scope_in: list[str] = Field(default_factory=list, max_length=500)
    scope_out: list[str] = Field(default_factory=list, max_length=500)


class ReleasePatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=300)
    version: str | None = Field(default=None, min_length=1, max_length=120)
    notes: str | None = Field(default=None, max_length=5000)
    planned_start_at: str | None = Field(default=None, max_length=80)
    planned_end_at: str | None = Field(default=None, max_length=80)
    scope_in: list[str] | None = Field(default=None, max_length=500)
    scope_out: list[str] | None = Field(default=None, max_length=500)


class ReleaseTransition(BaseModel):
    expected_revision: int = Field(ge=1)
    reason: str = Field(default="", max_length=2000)


class BuildCreate(BaseModel):
    identifier: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=120)
    release_id: str | None = Field(default=None, max_length=200)
    commit_ref: str | None = Field(default=None, max_length=300)
    notes: str = Field(default="", max_length=5000)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class BuildPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    notes: str | None = Field(default=None, max_length=5000)
    commit_ref: str | None = Field(default=None, max_length=300)


class EnvironmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    environment_type: Literal["development", "testing", "staging", "production", "custom"] = "testing"
    base_url: str | None = Field(default=None, max_length=2000)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    availability: Literal["AVAILABLE", "UNAVAILABLE", "MAINTENANCE"] = "AVAILABLE"
    secret_refs: dict[str, str] = Field(default_factory=dict)

    @field_validator("secret_refs")
    @classmethod
    def validate_secret_refs(cls, value):
        if any(not str(ref).startswith("secret://") for ref in value.values()):
            raise ValueError("Secret reference phải bắt đầu bằng secret://")
        return value


class EnvironmentPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=200)
    environment_type: Literal["development", "testing", "staging", "production", "custom"] | None = None
    base_url: str | None = Field(default=None, max_length=2000)
    capabilities: dict[str, Any] | None = None
    availability: Literal["AVAILABLE", "UNAVAILABLE", "MAINTENANCE"] | None = None


class EnvironmentSecretRefs(BaseModel):
    expected_revision: int = Field(ge=1)
    secret_refs: dict[str, str]

    @field_validator("secret_refs")
    @classmethod
    def validate_secret_refs(cls, value):
        if any(not str(ref).startswith("secret://") for ref in value.values()):
            raise ValueError("Secret reference phải bắt đầu bằng secret://")
        return value


class DeviceProfileInput(BaseModel):
    key: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    name: str = Field(min_length=2, max_length=200)
    device_type: Literal["desktop", "laptop", "tablet", "mobile", "other"]
    operating_system: str = Field(min_length=1, max_length=120)
    operating_system_version: str = Field(default="", max_length=120)
    browser: str = Field(default="", max_length=120)
    browser_version: str = Field(default="", max_length=120)
    viewport_width: int | None = Field(default=None, ge=1, le=20000)
    viewport_height: int | None = Field(default=None, ge=1, le=20000)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class DeviceMatrixCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=5000)
    profiles: list[DeviceProfileInput] = Field(min_length=1, max_length=500)

    @field_validator("profiles")
    @classmethod
    def validate_profile_keys(cls, value):
        keys = [item.key for item in value]
        if len(keys) != len(set(keys)):
            raise ValueError("Mã hồ sơ thiết bị không được trùng nhau")
        return value


class DeviceMatrixPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    profiles: list[DeviceProfileInput] | None = Field(default=None, min_length=1, max_length=500)

    @field_validator("profiles")
    @classmethod
    def validate_profile_keys(cls, value):
        if value is None:
            return value
        keys = [item.key for item in value]
        if len(keys) != len(set(keys)):
            raise ValueError("Mã hồ sơ thiết bị không được trùng nhau")
        return value


class DeviceMatrixArchive(BaseModel):
    expected_revision: int = Field(ge=1)
    reason: str = Field(min_length=2, max_length=2000)


class DeviceMatrixAssignment(BaseModel):
    target_type: Literal["test_plan", "test_run"]
    target_id: str = Field(min_length=1, max_length=200)
    expected_target_revision: int = Field(ge=1)
    profile_keys: list[str] = Field(default_factory=list, max_length=500)


class NotificationWatchInput(BaseModel):
    watching: bool = True


class ProjectNotificationRulePatch(BaseModel):
    expected_revision: int = Field(ge=0)
    enabled_events: list[str] = Field(default_factory=list, max_length=200)
    channels: list[Literal["in_app", "email", "webhook"]] = Field(
        default_factory=lambda: ["in_app"], max_length=3
    )
    target_roles: list[Literal["QA_LEAD", "TESTER", "BA", "DEVELOPER", "VIEWER"]] = Field(
        default_factory=lambda: ["QA_LEAD"], max_length=5
    )
    escalation_minutes: int | None = Field(default=None, ge=1, le=10080)


class ProjectNotificationPreferencePatch(BaseModel):
    expected_revision: int = Field(ge=0)
    digest_frequency: Literal["immediate", "daily", "weekly", "off"] = "immediate"
    channels: list[Literal["in_app", "email"]] = Field(
        default_factory=lambda: ["in_app"], max_length=2
    )
    muted_events: list[str] = Field(default_factory=list, max_length=200)
    quiet_hours_start: str | None = Field(
        default=None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$"
    )
    quiet_hours_end: str | None = Field(
        default=None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$"
    )
    timezone: str = Field(default="Asia/Ho_Chi_Minh", min_length=2, max_length=80)


class SecurityTestSuggestionInput(BaseModel):
    requirement_version_ids: list[str] = Field(default_factory=list, max_length=500)
    categories: list[
        Literal["authorization", "authentication", "input_validation", "session", "data_protection"]
    ] = Field(
        default_factory=lambda: ["authorization", "input_validation", "session"],
        min_length=1,
        max_length=5,
    )
    context: str = Field(default="", max_length=5000)
    idempotency_key: str = Field(min_length=8, max_length=200)


class PerformancePlanDraftInput(BaseModel):
    name: str = Field(min_length=2, max_length=300)
    objective: str = Field(default="", max_length=5000)
    requirement_version_ids: list[str] = Field(default_factory=list, max_length=500)
    workload_types: list[Literal["baseline", "load", "stress", "spike", "soak"]] = Field(
        default_factory=lambda: ["baseline", "load", "stress"],
        min_length=1,
        max_length=5,
    )
    target_virtual_users: int = Field(default=100, ge=1, le=1000000)
    target_requests_per_second: float | None = Field(default=None, gt=0, le=1000000)
    duration_minutes: int = Field(default=30, ge=1, le=10080)
    response_time_p95_ms: int | None = Field(default=None, ge=1, le=3600000)
    maximum_error_rate: float | None = Field(default=None, ge=0, le=1)
    context: str = Field(default="", max_length=5000)
    idempotency_key: str = Field(min_length=8, max_length=200)


class WebhookSubscriptionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    endpoint_reference: str = Field(min_length=12, max_length=500)
    secret_reference: str = Field(min_length=10, max_length=500)
    events: list[str] = Field(min_length=1, max_length=200)
    enabled: bool = True

    @model_validator(mode="after")
    def validate_references(self):
        if not self.endpoint_reference.startswith("endpoint://"):
            raise ValueError("Điểm cuối phải dùng endpoint reference của nền tảng")
        if not self.secret_reference.startswith("secret://"):
            raise ValueError("Bí mật phải dùng secret reference của nền tảng")
        return self


class WebhookSubscriptionPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=200)
    endpoint_reference: str | None = Field(default=None, min_length=12, max_length=500)
    secret_reference: str | None = Field(default=None, min_length=10, max_length=500)
    events: list[str] | None = Field(default=None, min_length=1, max_length=200)
    enabled: bool | None = None

    @model_validator(mode="after")
    def validate_references(self):
        if self.endpoint_reference is not None and not self.endpoint_reference.startswith(
            "endpoint://"
        ):
            raise ValueError("Điểm cuối phải dùng endpoint reference của nền tảng")
        if self.secret_reference is not None and not self.secret_reference.startswith(
            "secret://"
        ):
            raise ValueError("Bí mật phải dùng secret reference của nền tảng")
        return self


class WebhookReplayInput(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    reason: str = Field(min_length=2, max_length=2000)


class WebhookDeliveryRecordInput(BaseModel):
    delivery_id: str = Field(min_length=1, max_length=200)
    project_id: str = Field(min_length=1, max_length=200)
    subscription_id: str = Field(min_length=1, max_length=200)
    event_type: str = Field(min_length=1, max_length=200)
    status: Literal["DELIVERED", "FAILED"]
    attempt: int = Field(default=1, ge=1, le=1000)
    response_status: int | None = Field(default=None, ge=100, le=599)
    error_code: str | None = Field(default=None, max_length=200)
    payload_hash: str = Field(min_length=16, max_length=200)
    duration_ms: float | None = Field(default=None, ge=0, le=3600000)


class AutomationScriptGenerateInput(BaseModel):
    framework: Literal["playwright", "cypress", "selenium"]
    language: Literal["typescript", "javascript", "python"]
    test_case_version_id: str = Field(min_length=1, max_length=200)
    context: str = Field(default="", max_length=5000)
    idempotency_key: str = Field(min_length=8, max_length=200)

    @model_validator(mode="after")
    def validate_framework_language(self):
        if self.framework == "selenium" and self.language != "python":
            raise ValueError("Selenium chỉ hỗ trợ Python trong bản dựng này")
        if self.framework in {"playwright", "cypress"} and self.language == "python":
            raise ValueError("Playwright và Cypress dùng TypeScript hoặc JavaScript")
        return self


class AutomationScriptPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    source: str | None = Field(default=None, min_length=1, max_length=500000)
    filename: str | None = Field(default=None, min_length=1, max_length=300)
    secret_placeholders: list[str] | None = Field(default=None, max_length=100)
    review_note: str | None = Field(default=None, max_length=5000)


class AutomationScriptApproval(BaseModel):
    expected_revision: int = Field(ge=1)
    review_note: str = Field(min_length=2, max_length=5000)


class ProjectConnectorCreate(BaseModel):
    provider: Literal["jira", "github", "gitlab", "azure_devops"]
    connector_reference: str = Field(min_length=15, max_length=500)
    external_target: str = Field(min_length=2, max_length=500)
    confirm_external_target: bool
    field_mapping: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_platform_connector(self):
        if not self.connector_reference.startswith("connector://"):
            raise ValueError("Kết nối phải dùng tham chiếu connector của nền tảng")
        if not self.confirm_external_target:
            raise ValueError("Phải xác nhận chính xác đích bên ngoài")
        return self


class ProjectConnectorPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    external_target: str | None = Field(default=None, min_length=2, max_length=500)
    confirm_external_target: bool = False
    field_mapping: dict[str, str] | None = None
    enabled: bool | None = None

    @model_validator(mode="after")
    def validate_target_confirmation(self):
        if self.external_target is not None and not self.confirm_external_target:
            raise ValueError("Phải xác nhận chính xác đích bên ngoài")
        return self


class ProjectConnectorUnbind(BaseModel):
    expected_revision: int = Field(ge=1)
    reason: str = Field(min_length=2, max_length=2000)
    confirm_external_target: bool


class ConnectorSyncInput(BaseModel):
    direction: Literal["PULL", "PUSH", "BIDIRECTIONAL"]
    scopes: list[Literal["requirements", "defects", "statuses"]] = Field(
        min_length=1, max_length=3
    )
    idempotency_key: str = Field(min_length=8, max_length=200)


class ConnectorConflictResolution(BaseModel):
    expected_revision: int = Field(ge=1)
    resolution: Literal["KEEP_LOCAL", "KEEP_REMOTE", "MERGED"]
    merged_value: dict[str, Any] | None = None
    reason: str = Field(min_length=2, max_length=2000)

    @model_validator(mode="after")
    def validate_merged_value(self):
        if self.resolution == "MERGED" and self.merged_value is None:
            raise ValueError("Phải cung cấp dữ liệu đã hợp nhất")
        return self


class AutomationExecutionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=300)
    postman_artifact_id: str = Field(min_length=1, max_length=200)
    environment_id: str | None = Field(default=None, max_length=200)
    idempotency_key: str = Field(min_length=8, max_length=200)


class AutomationExecutionAction(BaseModel):
    expected_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)


class AutomationExecutionResultInput(BaseModel):
    execution_id: str = Field(min_length=1, max_length=200)
    operation_id: str = Field(min_length=1, max_length=200)
    status: Literal["COMPLETED", "FAILED", "CANCELLED"]
    summary: dict[str, Any] = Field(default_factory=dict)
    results: list[dict[str, Any]] = Field(default_factory=list, max_length=100000)
    logs: list[str] = Field(default_factory=list, max_length=10000)
    artifact_refs: list[str] = Field(default_factory=list, max_length=1000)
    context_signature: str = Field(min_length=64, max_length=64)


class CiCdBindingCreate(BaseModel):
    name: str = Field(min_length=2, max_length=300)
    connector_id: str = Field(min_length=1, max_length=200)
    pipeline_reference: str = Field(min_length=12, max_length=500)
    postman_artifact_id: str | None = Field(default=None, max_length=200)
    release_id: str | None = Field(default=None, max_length=200)
    test_case_version_ids: list[str] = Field(default_factory=list, max_length=5000)

    @field_validator("pipeline_reference")
    @classmethod
    def validate_pipeline_reference(cls, value):
        if not value.startswith("pipeline://"):
            raise ValueError("Pipeline phải dùng tham chiếu cấu hình của nền tảng")
        return value


class CiCdBindingPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=300)
    pipeline_reference: str | None = Field(default=None, min_length=12, max_length=500)
    postman_artifact_id: str | None = Field(default=None, max_length=200)
    release_id: str | None = Field(default=None, max_length=200)
    test_case_version_ids: list[str] | None = Field(default=None, max_length=5000)
    enabled: bool | None = None

    @field_validator("pipeline_reference")
    @classmethod
    def validate_optional_pipeline_reference(cls, value):
        if value is not None and not value.startswith("pipeline://"):
            raise ValueError("Pipeline phải dùng tham chiếu cấu hình của nền tảng")
        return value


class CiCdTriggerInput(BaseModel):
    project_id: str = Field(min_length=1, max_length=200)
    binding_id: str = Field(min_length=1, max_length=200)
    external_run_id: str = Field(min_length=1, max_length=300)
    commit_reference: str | None = Field(default=None, max_length=300)
    idempotency_key: str = Field(min_length=8, max_length=200)
    context_signature: str = Field(min_length=64, max_length=64)


class CiCdResultInput(BaseModel):
    project_id: str = Field(min_length=1, max_length=200)
    pipeline_run_id: str = Field(min_length=1, max_length=200)
    status: Literal["COMPLETED", "FAILED", "CANCELLED"]
    summary: dict[str, Any] = Field(default_factory=dict)
    results: list[dict[str, Any]] = Field(default_factory=list, max_length=100000)
    logs: list[str] = Field(default_factory=list, max_length=10000)
    context_signature: str = Field(min_length=64, max_length=64)


class CiCdRetryInput(BaseModel):
    expected_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)
    reason: str = Field(min_length=2, max_length=2000)


class CollaborationPresenceInput(BaseModel):
    artifact_type: Literal["requirement", "test_case"]
    artifact_id: str = Field(min_length=1, max_length=200)
    client_id: str = Field(min_length=8, max_length=200)


class CollaborationOperationInput(BaseModel):
    base_revision: int = Field(ge=1)
    operation_id: str = Field(min_length=8, max_length=200)
    changes: dict[str, Any] = Field(min_length=1, max_length=100)


class CollaborationConflictResolution(BaseModel):
    expected_revision: int = Field(ge=1)
    resolution: Literal["KEEP_CURRENT", "APPLY_INCOMING", "MERGED"]
    merged_changes: dict[str, Any] | None = None
    reason: str = Field(min_length=2, max_length=2000)

    @model_validator(mode="after")
    def validate_collaboration_merge(self):
        if self.resolution == "MERGED" and self.merged_changes is None:
            raise ValueError("Phải cung cấp nội dung hợp nhất")
        return self


class TestPlanPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=300)
    objective: str | None = Field(default=None, max_length=5000)
    scope_in: list[str] | None = Field(default=None, max_length=500)
    scope_out: list[str] | None = Field(default=None, max_length=500)
    environment: str | None = Field(default=None, max_length=200)
    environment_id: str | None = Field(default=None, max_length=200)
    entry_criteria: list[str] | None = Field(default=None, max_length=200)
    exit_criteria: list[str] | None = Field(default=None, max_length=200)
    risks: list[str] | None = Field(default=None, max_length=200)
    test_types: list[str] | None = Field(default=None, max_length=100)
    members: list[str] | None = Field(default=None, max_length=500)
    release: str | None = Field(default=None, max_length=200)
    release_id: str | None = Field(default=None, max_length=200)
    build: str | None = Field(default=None, max_length=200)
    build_id: str | None = Field(default=None, max_length=200)


class TestSuiteCreate(BaseModel):
    project_id: str
    name: str = Field(min_length=2, max_length=300)
    suite_type: Literal["smoke", "regression", "sanity", "feature", "api", "ui", "integration", "custom"]
    test_case_version_ids: list[str] = Field(default_factory=list, max_length=5000)


class TestSuitePatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=300)
    suite_type: Literal[
        "smoke", "regression", "sanity", "feature", "api", "ui", "integration", "custom"
    ] | None = None
    test_case_version_ids: list[str] | None = Field(default=None, max_length=5000)


class TestRunCreate(BaseModel):
    project_id: str
    name: str = Field(min_length=2, max_length=300)
    test_plan_id: str | None = None
    test_suite_ids: list[str] = Field(default_factory=list, max_length=500)
    test_case_version_ids: list[str] = Field(default_factory=list, max_length=5000)
    environment: str = Field(default="staging", max_length=200)
    environment_id: str | None = Field(default=None, max_length=200)
    release: str = Field(default="", max_length=200)
    release_id: str | None = Field(default=None, max_length=200)
    build: str = Field(default="", max_length=200)
    build_id: str | None = Field(default=None, max_length=200)


class TestRunPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=300)
    test_plan_id: str | None = None
    test_suite_ids: list[str] | None = Field(default=None, max_length=500)
    test_case_version_ids: list[str] | None = Field(default=None, max_length=5000)
    environment: str | None = Field(default=None, max_length=200)
    environment_id: str | None = Field(default=None, max_length=200)
    release: str | None = Field(default=None, max_length=200)
    release_id: str | None = Field(default=None, max_length=200)
    build: str | None = Field(default=None, max_length=200)
    build_id: str | None = Field(default=None, max_length=200)


class TestRunAssignmentInput(BaseModel):
    expected_revision: int = Field(ge=1)
    assignee_id: str = Field(min_length=1, max_length=200)
    test_case_assignments: dict[str, str] = Field(default_factory=dict)


class TestRunResumeInput(BaseModel):
    expected_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)


class TestStepResultInput(BaseModel):
    step_id: str = Field(min_length=1, max_length=200)
    status: Literal["PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"]
    actual_doc: dict[str, Any] = Field(default_factory=empty_doc)
    attachments: list[dict[str, Any]] = Field(default_factory=list, max_length=20)
    note: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def require_not_applicable_reason(self):
        if self.status == "NOT_APPLICABLE" and len(self.note.strip()) < 2:
            raise ValueError("Kết quả Không áp dụng của bước phải có lý do")
        return self


class TestResultInput(BaseModel):
    status: Literal["PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"]
    step_results: list[TestStepResultInput] = Field(default_factory=list, max_length=500)
    actual_result_doc: dict[str, Any] = Field(default_factory=empty_doc)
    attachments: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    note: str = Field(default="", max_length=5000)
    idempotency_key: str = Field(min_length=8, max_length=200)

    @model_validator(mode="after")
    def require_not_applicable_reason(self):
        if self.status == "NOT_APPLICABLE" and len(self.note.strip()) < 2:
            raise ValueError("Kết quả Không áp dụng phải có lý do")
        return self


class TestExecutionPatch(BaseModel):
    status: Literal["PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE", "IN_PROGRESS", "NOT_RUN"]
    step_results: list[TestStepResultInput] = Field(default_factory=list, max_length=500)
    actual_result_doc: dict[str, Any] = Field(default_factory=empty_doc)
    attachments: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    note: str = Field(default="", max_length=5000)
    idempotency_key: str = Field(min_length=8, max_length=200)
    expected_revision: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def require_not_applicable_reason(self):
        if self.status == "NOT_APPLICABLE" and len(self.note.strip()) < 2:
            raise ValueError("Kết quả Không áp dụng phải có lý do")
        return self


class TestResultCorrectionInput(BaseModel):
    status: Literal["PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"]
    reason: str = Field(min_length=2, max_length=2000)
    idempotency_key: str = Field(min_length=8, max_length=200)


class DefectCreate(BaseModel):
    project_id: str
    defect_key: str | None = Field(default=None, max_length=80)
    title: str = Field(min_length=2, max_length=300)
    description_doc: dict[str, Any] = Field(default_factory=empty_doc)
    steps_to_reproduce: list[dict[str, Any]] = Field(default_factory=list, max_length=500)
    actual_result_doc: dict[str, Any] = Field(default_factory=empty_doc)
    expected_result_doc: dict[str, Any] = Field(default_factory=empty_doc)
    severity: Literal["blocker", "critical", "major", "minor", "trivial"] = "major"
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    environment: str = Field(default="", max_length=500)
    environment_id: str | None = Field(default=None, max_length=200)
    release: str = Field(default="", max_length=200)
    release_id: str | None = Field(default=None, max_length=200)
    build: str = Field(default="", max_length=200)
    build_id: str | None = Field(default=None, max_length=200)
    assignee: str | None = None
    attachments: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    linked_test_result_id: str | None = None
    linked_test_case_version_id: str | None = None
    linked_requirement_version_ids: list[str] = Field(default_factory=list, max_length=200)


class DefectTransition(BaseModel):
    expected_revision: int = Field(ge=1)
    to_status: Literal[
        "NEW",
        "CONFIRMED",
        "IN_PROGRESS",
        "RESOLVED",
        "READY_FOR_RETEST",
        "REOPENED",
        "CLOSED",
        "REJECTED",
        "DUPLICATE",
    ]
    reason: str = Field(min_length=2, max_length=2000)


class DefectRetestInput(BaseModel):
    test_result_id: str = Field(min_length=1, max_length=200)
    expected_revision: int = Field(ge=1)
    note: str = Field(default="", max_length=5000)
    idempotency_key: str = Field(min_length=8, max_length=200)


class BugTraceSuggestionInput(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)


class DefectTraceUpdateInput(BaseModel):
    expected_revision: int = Field(ge=1)
    reason: str = Field(min_length=2, max_length=2000)
    linked_test_result_id: str | None = Field(default=None, max_length=200)
    linked_test_case_version_id: str | None = Field(default=None, max_length=200)
    linked_requirement_version_ids: list[str] | None = Field(default=None, max_length=200)
    ai_result_id: str | None = Field(default=None, max_length=200)
    accepted_candidate_ids: list[str] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def require_trace_change(self):
        trace_fields = {
            "linked_test_result_id",
            "linked_test_case_version_id",
            "linked_requirement_version_ids",
        }
        if not trace_fields & self.model_fields_set:
            raise ValueError("Phải chọn ít nhất một liên kết truy vết cần thay đổi")
        return self


class GenerateInput(BaseModel):
    categories: list[str] = Field(default_factory=list, max_length=20)
    count_per_category: int = Field(default=1, ge=1, le=20)
    instruction: str = Field(default="", max_length=5000)


class TestCaseGenerateInput(GenerateInput):
    requirement_version_id: str = Field(min_length=1, max_length=200)


class SearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    artifact_types: list[str] = Field(default_factory=list, max_length=20)
    limit: int = Field(default=20, ge=1, le=100)


class ProjectQuestionInput(BaseModel):
    question: str = Field(min_length=2, max_length=5000)
    artifact_types: list[str] = Field(default_factory=list, max_length=20)
    evidence_limit: int = Field(default=20, ge=1, le=50)


class BulkTagInput(BaseModel):
    artifact_type: Literal["requirement", "test_case"]
    ids: list[str] = Field(min_length=1, max_length=5000)
    add_tags: list[str] = Field(default_factory=list, max_length=100)
    remove_tags: list[str] = Field(default_factory=list, max_length=100)
    preview: bool = False
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class BulkSuiteInput(BaseModel):
    suite_id: str = Field(min_length=1, max_length=200)
    test_case_ids: list[str] = Field(min_length=1, max_length=5000)
    expected_revision: int = Field(ge=1)
    preview: bool = False
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class BulkReviewRequiredInput(BaseModel):
    test_case_ids: list[str] = Field(min_length=1, max_length=5000)
    reason: str = Field(min_length=2, max_length=2000)
    preview: bool = False
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class BulkArchiveInput(BaseModel):
    artifact_type: Literal["requirement", "test_case"]
    ids: list[str] = Field(min_length=1, max_length=5000)
    reason: str = Field(min_length=2, max_length=2000)
    preview: bool = False
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class BulkProposalGenerateInput(BaseModel):
    impact_analysis_ids: list[str] = Field(min_length=1, max_length=5000)
    preview: bool = False
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class BulkProposalApproveInput(BaseModel):
    proposal_ids: list[str] = Field(min_length=1, max_length=5000)
    review_note: str = Field(min_length=2, max_length=2000)
    preview: bool = False
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)
