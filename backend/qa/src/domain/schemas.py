from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


def empty_doc():
    return {"type": "doc", "content": []}


class ProjectCreate(BaseModel):
    key: str = Field(min_length=2, max_length=30, pattern=r"^[A-Z][A-Z0-9_-]+$")
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=5000)
    project_type: Literal["web", "mobile", "api", "desktop", "embedded", "other"] = "web"
    settings: dict[str, Any] = Field(default_factory=dict)


class ProjectPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
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


class ReviewTransitionInput(BaseModel):
    expected_revision: int = Field(ge=1)
    review_note: str = Field(default="", max_length=2000)


class RequirementCompareInput(BaseModel):
    from_version_id: str
    to_version_id: str


class ImportCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=300)
    format: Literal["pdf", "docx", "md", "txt", "csv", "xlsx", "openapi", "postman"]
    content: str | dict[str, Any] | list[Any]


class RequirementExtractionInput(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)


class RequirementParseRetry(BaseModel):
    expected_revision: int = Field(ge=1)


class ReviewCommentCreate(BaseModel):
    artifact_type: str = Field(min_length=1, max_length=80)
    artifact_id: str = Field(min_length=1, max_length=200)
    body_doc: dict[str, Any] = Field(default_factory=empty_doc)
    anchor: dict[str, Any] | None = None
    parent_comment_id: str | None = None


class ReviewCommentAction(BaseModel):
    reason: str = Field(default="", max_length=2000)


class ImportConfirm(BaseModel):
    selected_indexes: list[int] = Field(default_factory=list, max_length=2000)
    expected_revision: int | None = Field(default=None, ge=1)


class RequirementCandidateReview(RequirementCreate):
    extraction_confidence: float = Field(default=1, ge=0, le=1)
    candidate_relation: str | None = Field(default=None, max_length=80)


class RequirementImportReview(BaseModel):
    expected_revision: int = Field(ge=1)
    preview: list[RequirementCandidateReview] = Field(min_length=1, max_length=500)
    review_note: str = Field(default="", max_length=2000)


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
    entry_criteria: list[str] = Field(default_factory=list, max_length=200)
    exit_criteria: list[str] = Field(default_factory=list, max_length=200)
    risks: list[str] = Field(default_factory=list, max_length=200)
    test_types: list[str] = Field(default_factory=list, max_length=100)
    members: list[str] = Field(default_factory=list, max_length=500)
    release: str = Field(default="", max_length=200)
    build: str = Field(default="", max_length=200)


class TestSuiteCreate(BaseModel):
    project_id: str
    name: str = Field(min_length=2, max_length=300)
    suite_type: Literal["smoke", "regression", "sanity", "feature", "api", "ui", "integration", "custom"]
    test_case_version_ids: list[str] = Field(default_factory=list, max_length=5000)


class TestRunCreate(BaseModel):
    project_id: str
    name: str = Field(min_length=2, max_length=300)
    test_plan_id: str | None = None
    test_suite_ids: list[str] = Field(default_factory=list, max_length=500)
    test_case_version_ids: list[str] = Field(default_factory=list, max_length=5000)
    environment: str = Field(default="staging", max_length=200)
    release: str = Field(default="", max_length=200)
    build: str = Field(default="", max_length=200)


class TestStepResultInput(BaseModel):
    step_id: str = Field(min_length=1, max_length=200)
    status: Literal["PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"]
    actual_doc: dict[str, Any] = Field(default_factory=empty_doc)
    attachments: list[dict[str, Any]] = Field(default_factory=list, max_length=20)
    note: str = Field(default="", max_length=2000)


class TestResultInput(BaseModel):
    status: Literal["PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"]
    step_results: list[TestStepResultInput] = Field(default_factory=list, max_length=500)
    actual_result_doc: dict[str, Any] = Field(default_factory=empty_doc)
    attachments: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    note: str = Field(default="", max_length=5000)
    idempotency_key: str = Field(min_length=8, max_length=200)


class TestExecutionPatch(BaseModel):
    status: Literal["PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE", "IN_PROGRESS", "NOT_RUN"]
    step_results: list[TestStepResultInput] = Field(default_factory=list, max_length=500)
    actual_result_doc: dict[str, Any] = Field(default_factory=empty_doc)
    attachments: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    note: str = Field(default="", max_length=5000)
    idempotency_key: str = Field(min_length=8, max_length=200)
    expected_revision: int | None = Field(default=None, ge=1)


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
    release: str = Field(default="", max_length=200)
    build: str = Field(default="", max_length=200)
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


class BulkTagInput(BaseModel):
    artifact_type: Literal["requirement", "test_case"]
    ids: list[str] = Field(min_length=1, max_length=5000)
    add_tags: list[str] = Field(default_factory=list, max_length=100)
    remove_tags: list[str] = Field(default_factory=list, max_length=100)


class BulkSuiteInput(BaseModel):
    suite_id: str = Field(min_length=1, max_length=200)
    test_case_ids: list[str] = Field(min_length=1, max_length=5000)
    expected_revision: int = Field(ge=1)


class BulkReviewRequiredInput(BaseModel):
    test_case_ids: list[str] = Field(min_length=1, max_length=5000)
    reason: str = Field(min_length=2, max_length=2000)


class BulkArchiveInput(BaseModel):
    artifact_type: Literal["requirement", "test_case"]
    ids: list[str] = Field(min_length=1, max_length=5000)
    reason: str = Field(min_length=2, max_length=2000)


class BulkProposalGenerateInput(BaseModel):
    impact_analysis_ids: list[str] = Field(min_length=1, max_length=5000)


class BulkProposalApproveInput(BaseModel):
    proposal_ids: list[str] = Field(min_length=1, max_length=5000)
    review_note: str = Field(min_length=2, max_length=2000)
