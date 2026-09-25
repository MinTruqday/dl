from typing import Annotated, Any, List, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RetrievalExpansionRequest(BaseModel):
    question: str = Field(
        min_length=1, max_length=10000, description="Question to expand for semantic retrieval"
    )


class CrossDocumentExpansionRequest(BaseModel):
    question: str = Field(
        min_length=1, max_length=10000, description="Question to decompose across documents"
    )
    document_ids: List[Annotated[str, Field(min_length=1, max_length=128)]] = Field(
        min_length=2, max_length=100, description="Ordered document identifiers to retrieve"
    )


class KnowledgeChunkSafetyRequest(BaseModel):
    texts: List[Annotated[str, Field(min_length=1, max_length=4000)]] = Field(
        min_length=1, max_length=500, description="Retrieved chunks to assess for safety"
    )


class KnowledgeDocumentSummaryRequest(BaseModel):
    text: str = Field(
        min_length=1, max_length=15000, description="Document content to summarize for knowledge retrieval"
    )


class TestingEvidence(BaseModel):
    model_config = ConfigDict(extra="allow")

    artifact_type: str = Field(min_length=1, max_length=100)
    artifact_id: str | None = Field(default=None, min_length=1, max_length=200)
    artifact_version_id: str | None = Field(default=None, min_length=1, max_length=200)
    authority: str | None = Field(default=None, min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=4000)

    @model_validator(mode="after")
    def require_identifier(self):
        if not self.artifact_id and not self.artifact_version_id:
            raise ValueError("testing_evidence_identifier_required")
        return self


class TestingAssistanceRequest(BaseModel):
    capability: Literal[
        "project_question",
        "requirement_quality_analysis",
        "scenario_generation",
        "test_generation",
        "impact_analysis",
        "security_test_generation",
        "performance_plan_generation",
        "automation_script_generation",
        "test_condition_generation",
        "causal_analysis",
        "status_report_narrative",
        "completion_report_narrative",
        "lessons_learned_clustering",
    ] = Field(description="Testing capability to perform")
    project_id: str = Field(
        min_length=1, max_length=128, description="Project identifier that bounds the operation"
    )
    instruction: str = Field(
        default="", max_length=5000, description="Additional user business instruction"
    )
    evidence: List[TestingEvidence] = Field(
        min_length=1,
        max_length=100,
        description="Artifact evidence already bounded to the project",
    )


class TestingAssistanceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: str = Field(description="Executed testing capability")
    suggestions: List[dict[str, Any]] = Field(
        default_factory=list,
        max_length=100,
        description="Proposals that remain pending review",
    )
    findings: List[dict[str, Any]] = Field(
        default_factory=list,
        max_length=100,
        description="Analysis findings pending acknowledgement",
    )
    evidence_refs: List[str] = Field(
        default_factory=list, max_length=200, description="Evidence identifiers supporting the result"
    )
    confidence: float = Field(ge=0, le=1, description="Model confidence for reference")
    warnings: List[str] = Field(
        default_factory=list, max_length=50, description="Evidence limitation and conflict warnings"
    )
    status: Literal["SUCCESS", "DEGRADED"] = Field(
        default="SUCCESS", description="AI capability operating status"
    )
    degraded_mode: str | None = Field(
        default=None, description="Fallback mode when the provider or retrieval is unavailable"
    )
    provider: str = Field(min_length=1, max_length=100, description="Provider that produced the result")
    model: dict[str, Any] = Field(
        default_factory=dict, description="Model prompt and tool schema version metadata"
    )
    prompt_version: str = Field(min_length=1, max_length=100, description="Prompt version")
    tool_schema_version: str = Field(
        min_length=1, max_length=100, description="Output schema version"
    )
    retrieval_version: str = Field(
        min_length=1, max_length=100, description="Evidence retrieval version"
    )
    created_at: str = Field(min_length=1, max_length=100, description="Result creation time")
    reason_codes: List[str] = Field(
        default_factory=list,
        max_length=100,
        description="Auditable reason codes without hidden reasoning",
    )
    workflow: dict[str, Any] = Field(
        default_factory=dict, description="Auditable observe reason act observe workflow state"
    )
    answer: str = Field(
        default="", max_length=20000, description="Evidence grounded answer for project questions"
    )


class ProjectQuestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["project_question"]
    answer: str = Field(min_length=1, max_length=4000)
    evidence_refs: List[str] = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)


class RequirementQualityFindingOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Literal[
        "AMBIGUITY",
        "OMISSION",
        "INCONSISTENCY",
        "CONTRADICTION",
        "UNTESTABLE",
        "MISSING_ACCEPTANCE_CRITERIA",
        "MISSING_ERROR_BEHAVIOR",
        "MISSING_PERMISSION_RULE",
        "MISSING_BOUNDARY",
        "MISSING_STATE_RULE",
        "MISSING_DATA_RULE",
        "MISSING_NON_FUNCTIONAL_CRITERIA",
        "OTHER",
    ]
    severity: Literal["error", "warning", "info"]
    message: str = Field(min_length=2, max_length=5000)
    suggestion: str = Field(min_length=2, max_length=5000)
    evidence_refs: List[str] = Field(min_length=1, max_length=100)
    reason_codes: List[str] = Field(min_length=1, max_length=100)


class RequirementAcceptanceCriterionSuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1, max_length=80)
    content: str = Field(min_length=2, max_length=5000)


class RequirementRevisionSuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revised_title: str | None = Field(min_length=2, max_length=300)
    revised_content: str | None = Field(min_length=2, max_length=20000)
    revised_actors: List[str] | None = Field(min_length=1, max_length=100)
    revised_business_rules: List[str] | None = Field(min_length=1, max_length=200)
    revised_acceptance_criteria: List[RequirementAcceptanceCriterionSuggestionOutput] | None = (
        Field(min_length=1, max_length=200)
    )
    revised_dependencies: List[str] | None = Field(max_length=200)
    target_fields: List[
        Literal[
            "title", "content", "actors", "business_rules", "acceptance_criteria", "dependencies"
        ]
    ] = Field(min_length=1, max_length=6)
    rationale: str = Field(min_length=2, max_length=5000)
    evidence_refs: List[str] = Field(min_length=1, max_length=100)
    reason_codes: List[str] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def require_revision_value(self):
        values = {
            "title": self.revised_title,
            "content": self.revised_content,
            "actors": self.revised_actors,
            "business_rules": self.revised_business_rules,
            "acceptance_criteria": self.revised_acceptance_criteria,
            "dependencies": self.revised_dependencies,
        }
        revised_fields = {field for field, value in values.items() if value is not None}
        if not revised_fields:
            raise ValueError("requirement_revision_value_required")
        if len(self.target_fields) != len(set(self.target_fields)):
            raise ValueError("requirement_revision_target_fields_duplicate")
        if set(self.target_fields) != revised_fields:
            raise ValueError("requirement_revision_target_fields_mismatch")
        for values in (self.revised_actors, self.revised_business_rules):
            if values is not None and any(not value.strip() for value in values):
                raise ValueError("requirement_revision_blank_list_value")
        return self


class RequirementQualityOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["requirement_quality_analysis"]
    findings: List[RequirementQualityFindingOutput] = Field(default_factory=list, max_length=100)
    suggestions: List[RequirementRevisionSuggestionOutput] = Field(
        default_factory=list, max_length=1
    )
    evidence_refs: List[str] = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)


class GeneratedStepOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str = Field(min_length=2, max_length=5000)
    expected: str = Field(min_length=2, max_length=5000)
    test_data: dict[str, Any] = Field(default_factory=dict)


class GeneratedCaseOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=2, max_length=300)
    category: str = Field(min_length=2, max_length=100)
    objective: str = Field(min_length=2, max_length=5000)
    preconditions: str = Field(min_length=2, max_length=5000)
    steps: List[GeneratedStepOutput] = Field(min_length=1, max_length=50)
    expected: str = Field(min_length=2, max_length=5000)
    acceptance_criterion_ids: List[str] = Field(default_factory=list, max_length=100)


class GeneratedCasesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["scenario_generation", "test_generation"]
    suggestions: List[GeneratedCaseOutput] = Field(min_length=1, max_length=100)
    evidence_refs: List[str] = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)


class TestConditionSuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=2, max_length=300)
    description: str = Field(min_length=2, max_length=5000)
    category: Literal["POSITIVE", "NEGATIVE", "BOUNDARY"]
    coverage_item: str = Field(min_length=1, max_length=500)
    test_level: str = Field(min_length=1, max_length=100)
    test_type: str = Field(min_length=1, max_length=100)
    risk: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    technique_candidates: List[str] = Field(default_factory=list, max_length=100)
    testability_status: Literal["TESTABLE", "CONDITIONALLY_TESTABLE", "UNTESTABLE"]


class TestConditionSuggestionsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["test_condition_generation"]
    condition_candidates: List[TestConditionSuggestionOutput] = Field(min_length=1, max_length=100)
    evidence_refs: List[str] = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def require_coverage_categories(self):
        categories = {candidate.category for candidate in self.condition_candidates}
        required = {"POSITIVE", "NEGATIVE", "BOUNDARY"}
        if not required.issubset(categories):
            raise ValueError("test_condition_category_coverage_required")
        return self


class ImpactClassificationSuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_case_version_id: str = Field(min_length=1, max_length=128)
    classification: Literal["STILL_VALID", "POTENTIALLY_AFFECTED", "NEEDS_UPDATE", "OBSOLETE"]
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(min_length=2, max_length=5000)
    maintenance_patch: "MaintenanceTestCasePatchOutput | None" = None

    @model_validator(mode="after")
    def require_patch_for_update(self):
        if self.classification == "NEEDS_UPDATE" and self.maintenance_patch is None:
            raise ValueError("maintenance_patch_required")
        return self


class MaintenanceTestStepOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str = Field(min_length=2, max_length=5000)
    expected: str = Field(min_length=2, max_length=5000)
    test_data: dict = Field(default_factory=dict)


class MaintenanceTestCasePatchOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=2, max_length=300)
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
    ] | None = None
    objective: str | None = Field(default=None, min_length=2, max_length=5000)
    preconditions: str | None = Field(default=None, min_length=2, max_length=5000)
    steps: List[MaintenanceTestStepOutput] | None = Field(default=None, min_length=1, max_length=100)
    expected: str | None = Field(default=None, min_length=2, max_length=5000)
    test_data: dict | None = None

    @model_validator(mode="after")
    def require_patch_value(self):
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("maintenance_patch_value_required")
        return self


class NewTestCandidateOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=2, max_length=5000)
    confidence: float = Field(ge=0, le=1)
    patch: MaintenanceTestCasePatchOutput

    @model_validator(mode="after")
    def require_complete_test_case(self):
        if not self.patch.title or not self.patch.steps or not self.patch.expected:
            raise ValueError("new_test_candidate_incomplete")
        return self


ImpactClassificationSuggestionOutput.model_rebuild()


class ImpactClassificationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["impact_analysis"]
    suggestions: List[ImpactClassificationSuggestionOutput] = Field(min_length=1, max_length=100)
    new_test_candidates: List[NewTestCandidateOutput] = Field(default_factory=list, max_length=100)
    evidence_refs: List[str] = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)


class SecuritySuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Literal[
        "authorization", "authentication", "input_validation", "session", "data_protection"
    ]
    title: str = Field(min_length=2, max_length=300)
    preconditions: List[str] = Field(min_length=1, max_length=30)
    action: str = Field(min_length=2, max_length=5000)
    expected: str = Field(min_length=2, max_length=5000)
    requirement_version_ids: List[str] = Field(default_factory=list, max_length=100)


class SecuritySuggestionsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["security_test_generation"]
    suggestions: List[SecuritySuggestionOutput] = Field(min_length=1, max_length=100)
    evidence_refs: List[str] = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)


class PerformanceSuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workload_type: Literal["baseline", "load", "stress", "spike", "soak"]
    title: str = Field(min_length=2, max_length=300)
    virtual_users: int = Field(ge=1, le=1000000)
    requests_per_second: float | None = Field(default=None, gt=0)
    duration_minutes: int = Field(ge=1, le=10080)
    ramp_pattern: str = Field(min_length=2, max_length=2000)
    actions: List[str] = Field(min_length=1, max_length=50)
    expected: str = Field(min_length=2, max_length=5000)


class PerformanceSuggestionsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["performance_plan_generation"]
    suggestions: List[PerformanceSuggestionOutput] = Field(min_length=1, max_length=100)
    evidence_refs: List[str] = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)


class AutomationScriptSuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1, max_length=100000)
    secret_placeholders: List[str] = Field(default_factory=list, max_length=100)


class AutomationScriptOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["automation_script_generation"]
    suggestions: List[AutomationScriptSuggestionOutput] = Field(min_length=1, max_length=1)
    evidence_refs: List[str] = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)


class CausalHypothesisSuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root_cause_category: Literal[
        "REQUIREMENT",
        "DESIGN",
        "IMPLEMENTATION",
        "CONFIGURATION",
        "TEST_DATA",
        "TEST_CASE_GAP",
        "ENVIRONMENT",
        "INTEGRATION",
        "DEPLOYMENT",
        "PROCESS",
        "THIRD_PARTY",
        "UNKNOWN",
    ]
    hypothesis: str = Field(min_length=2, max_length=5000)
    contributing_factors: List[str] = Field(default_factory=list, max_length=50)
    five_whys: List[str] = Field(default_factory=list, max_length=5)
    missing_test_conditions: List[str] = Field(default_factory=list, max_length=50)
    missing_test_cases: List[str] = Field(default_factory=list, max_length=50)
    evidence_refs: List[str] = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)


class CausalHypothesesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["causal_analysis"]
    suggestions: List[CausalHypothesisSuggestionOutput] = Field(min_length=1, max_length=100)
    evidence_refs: List[str] = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)


class StatusReportNarrativeSuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: str = Field(min_length=2, max_length=10000)
    progress_summary: str = Field(min_length=2, max_length=10000)
    coverage_summary: str = Field(min_length=2, max_length=10000)
    defect_summary: str = Field(min_length=2, max_length=10000)
    forecast: str = Field(min_length=2, max_length=10000)
    recommendation: Literal[
        "ON_TRACK", "AT_RISK", "BLOCKED", "CONTINUE_TESTING", "READY_WITH_RISK", "NOT_READY"
    ]


class StatusReportNarrativeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["status_report_narrative"]
    suggestions: List[StatusReportNarrativeSuggestionOutput] = Field(min_length=1, max_length=1)
    evidence_refs: List[str] = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)


class CompletionReportNarrativeSuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: str = Field(min_length=2, max_length=10000)
    closure_summary: str = Field(min_length=2, max_length=10000)
    residual_risk_summary: str = Field(min_length=2, max_length=10000)
    recommendation_rationale: str = Field(min_length=2, max_length=10000)


class CompletionReportNarrativeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["completion_report_narrative"]
    suggestions: List[CompletionReportNarrativeSuggestionOutput] = Field(min_length=1, max_length=1)
    evidence_refs: List[str] = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)


class LessonsLearnedClusterSuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme: str = Field(min_length=2, max_length=500)
    category: Literal["WORKED", "FAILED", "BLOCKER", "IMPROVEMENT"]
    summary: str = Field(min_length=2, max_length=5000)
    source_indices: List[int] = Field(min_length=1, max_length=500)
    improvement_candidates: List[str] = Field(default_factory=list, max_length=100)


class LessonsLearnedClustersOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["lessons_learned_clustering"]
    suggestions: List[LessonsLearnedClusterSuggestionOutput] = Field(min_length=1, max_length=100)
    evidence_refs: List[str] = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)
