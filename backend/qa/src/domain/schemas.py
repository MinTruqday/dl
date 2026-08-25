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
    status: Literal["active", "archived"] | None = None
    settings: dict[str, Any] | None = None
    member_roles: dict[str, str] | None = None


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


class RequirementVersionCreate(RequirementCreate):
    change_reason: str = Field(min_length=2, max_length=2000)
    expected_current_version_id: str


class RequirementBaselineInput(BaseModel):
    expected_revision: int = Field(ge=1)


class RequirementCompareInput(BaseModel):
    from_version_id: str
    to_version_id: str


class ImportCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=300)
    format: Literal["pdf", "docx", "md", "txt", "csv", "xlsx", "openapi", "postman"]
    content: str | dict[str, Any] | list[Any]


class ImportConfirm(BaseModel):
    selected_indexes: list[int] = Field(default_factory=list, max_length=2000)


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
    preconditions_doc: dict[str, Any] = Field(default_factory=empty_doc)
    steps: list[TestStep] = Field(default_factory=list, max_length=500)
    test_data: dict[str, Any] = Field(default_factory=dict)
    expected_result_doc: dict[str, Any] = Field(default_factory=empty_doc)
    postconditions_doc: dict[str, Any] = Field(default_factory=empty_doc)
    tags: list[str] = Field(default_factory=list, max_length=100)
    automation_status: Literal["manual", "candidate", "automated"] = "manual"
    requirement_version_ids: list[str] = Field(default_factory=list, max_length=200)
    acceptance_criterion_ids: list[str] = Field(default_factory=list, max_length=500)
    scenario_id: str | None = None
    origin: Literal["manual", "ai_generated", "clone", "import", "maintenance"] = "manual"
    source_evidence: list[dict[str, Any]] = Field(default_factory=list, max_length=200)

    @field_validator(
        "preconditions_doc",
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
    preconditions_doc: dict[str, Any] | None = None
    steps: list[TestStep] | None = None
    test_data: dict[str, Any] | None = None
    expected_result_doc: dict[str, Any] | None = None
    postconditions_doc: dict[str, Any] | None = None
    tags: list[str] | None = None
    automation_status: str | None = None
    requirement_version_ids: list[str] | None = None
    acceptance_criterion_ids: list[str] | None = None
    scenario_id: str | None = None


class TestCaseFreezeInput(BaseModel):
    expected_revision: int = Field(ge=1)
    change_reason: str = Field(default="Phê duyệt phiên bản kiểm thử", max_length=2000)


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
    build: str = Field(default="", max_length=200)


class TestResultInput(BaseModel):
    status: Literal["PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"]
    step_results: list[dict[str, Any]] = Field(default_factory=list, max_length=500)
    attachments: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    note: str = Field(default="", max_length=5000)
    idempotency_key: str = Field(min_length=8, max_length=200)


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
    build: str = Field(default="", max_length=200)
    assignee: str | None = None
    attachments: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    linked_test_result_id: str | None = None
    linked_test_case_version_id: str | None = None
    linked_requirement_version_ids: list[str] = Field(default_factory=list, max_length=200)


class DefectTransition(BaseModel):
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


class GenerateInput(BaseModel):
    categories: list[str] = Field(default_factory=list, max_length=20)
    count_per_category: int = Field(default=1, ge=1, le=20)
    instruction: str = Field(default="", max_length=5000)


class SearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    artifact_types: list[str] = Field(default_factory=list, max_length=20)
    limit: int = Field(default=20, ge=1, le=100)
