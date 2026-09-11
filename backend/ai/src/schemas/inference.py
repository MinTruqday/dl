from typing import Annotated, Any, List, Literal

from pydantic import BaseModel, ConfigDict, Field


class RetrievalExpansionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000, description="Câu hỏi cần mở rộng cho truy xuất ngữ nghĩa")


class CrossDocumentExpansionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000, description="Câu hỏi cần phân rã theo từng tài liệu")
    document_ids: List[Annotated[str, Field(min_length=1, max_length=128)]] = Field(min_length=2, max_length=100, description="Danh sách tài liệu theo thứ tự cần truy xuất")


class KnowledgeChunkSafetyRequest(BaseModel):
    texts: List[Annotated[str, Field(min_length=1, max_length=4000)]] = Field(min_length=1, max_length=500, description="Các đoạn truy xuất cần kiểm tra an toàn")


class KnowledgeDocumentSummaryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=15000, description="Nội dung tài liệu cần tóm tắt cho knowledge")


class TestingAssistanceRequest(BaseModel):
    capability: Literal["project_question", "requirement_lint", "scenario_generation", "test_generation", "trace_recommendation", "semantic_change", "impact_analysis", "maintenance_proposal", "regression_recommendation", "defect_linking", "security_test_generation", "performance_plan_generation", "automation_script_generation", "test_condition_generation", "causal_analysis", "status_report_narrative", "completion_report_narrative", "lessons_learned_clustering"] = Field(description="Năng lực kiểm thử cần thực hiện")
    project_id: str = Field(min_length=1, max_length=128, description="Mã Project giới hạn phạm vi xử lý")
    instruction: str = Field(default="", max_length=5000, description="Chỉ dẫn nghiệp vụ bổ sung của người dùng")
    evidence: List[dict[str, Any]] = Field(min_length=1, max_length=100, description="Bằng chứng artifact đã được giới hạn theo Project")


class TestingAssistanceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: str = Field(description="Năng lực kiểm thử đã thực hiện")
    suggestions: List[dict[str, Any]] = Field(default_factory=list, max_length=100, description="Danh sách đề xuất chỉ ở trạng thái chờ duyệt")
    evidence_refs: List[str] = Field(default_factory=list, max_length=200, description="Mã bằng chứng hỗ trợ kết quả")
    confidence: float = Field(ge=0, le=1, description="Độ tin cậy tham khảo của mô hình")
    warnings: List[str] = Field(default_factory=list, max_length=50, description="Cảnh báo giới hạn và xung đột bằng chứng")
    status: Literal["SUCCESS", "DEGRADED"] = Field(default="SUCCESS", description="Trạng thái vận hành của năng lực AI")
    degraded_mode: str | None = Field(default=None, description="Chế độ fallback khi provider hoặc retrieval không sẵn sàng")
    model: dict[str, Any] = Field(default_factory=dict, description="Metadata version của model prompt và tool schema")
    reason_codes: List[str] = Field(default_factory=list, max_length=100, description="Mã lý do có thể audit không chứa hidden reasoning")
    workflow: dict[str, Any] = Field(default_factory=dict, description="Trạng thái Observe Reason Act Observe có thể audit")
    answer: str = Field(default="", max_length=20000, description="Câu trả lời có căn cứ dùng cho hỏi đáp Project")


class ProjectQuestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["project_question"]
    answer: str = Field(min_length=1, max_length=4000)
    evidence_refs: List[str] = Field(default_factory=list, max_length=200)
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
    evidence_refs: List[str] = Field(default_factory=list, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)


class TestConditionSuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=2, max_length=300)
    coverage_item: str = Field(min_length=1, max_length=500)
    test_level: str = Field(min_length=1, max_length=100)
    test_type: str = Field(min_length=1, max_length=100)
    risk: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    technique_candidates: List[str] = Field(default_factory=list, max_length=100)
    testability_status: Literal["TESTABLE", "CONDITIONALLY_TESTABLE", "UNTESTABLE"]
    analysis_findings: List[dict[str, Any]] = Field(default_factory=list, max_length=100)


class TestConditionSuggestionsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["test_condition_generation"]
    suggestions: List[TestConditionSuggestionOutput] = Field(min_length=1, max_length=100)
    evidence_refs: List[str] = Field(default_factory=list, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)


class SecuritySuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Literal["authorization", "authentication", "input_validation", "session", "data_protection"]
    title: str = Field(min_length=2, max_length=300)
    preconditions: List[str] = Field(min_length=1, max_length=30)
    action: str = Field(min_length=2, max_length=5000)
    expected: str = Field(min_length=2, max_length=5000)
    requirement_version_ids: List[str] = Field(default_factory=list, max_length=100)


class SecuritySuggestionsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["security_test_generation"]
    suggestions: List[SecuritySuggestionOutput] = Field(min_length=1, max_length=100)
    evidence_refs: List[str] = Field(default_factory=list, max_length=200)
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
    evidence_refs: List[str] = Field(default_factory=list, max_length=200)
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
    evidence_refs: List[str] = Field(default_factory=list, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)


class CausalHypothesisSuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root_cause_category: Literal["REQUIREMENT", "DESIGN", "IMPLEMENTATION", "CONFIGURATION", "TEST_DATA", "TEST_CASE_GAP", "ENVIRONMENT", "INTEGRATION", "DEPLOYMENT", "PROCESS", "UNKNOWN"]
    hypothesis: str = Field(min_length=2, max_length=5000)
    contributing_factors: List[str] = Field(default_factory=list, max_length=50)
    five_whys: List[str] = Field(default_factory=list, max_length=5)
    missing_test_conditions: List[str] = Field(default_factory=list, max_length=50)
    missing_test_cases: List[str] = Field(default_factory=list, max_length=50)
    evidence_refs: List[str] = Field(default_factory=list, max_length=200)
    confidence: float = Field(ge=0, le=1)


class CausalHypothesesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["causal_analysis"]
    suggestions: List[CausalHypothesisSuggestionOutput] = Field(min_length=1, max_length=100)
    evidence_refs: List[str] = Field(default_factory=list, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)


class StatusReportNarrativeSuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: str = Field(min_length=2, max_length=10000)
    progress_summary: str = Field(min_length=2, max_length=10000)
    coverage_summary: str = Field(min_length=2, max_length=10000)
    defect_summary: str = Field(min_length=2, max_length=10000)
    forecast: str = Field(min_length=2, max_length=10000)
    recommendation: Literal["ON_TRACK", "AT_RISK", "BLOCKED", "CONTINUE_TESTING", "READY_WITH_RISK", "NOT_READY"]


class StatusReportNarrativeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Literal["status_report_narrative"]
    suggestions: List[StatusReportNarrativeSuggestionOutput] = Field(min_length=1, max_length=1)
    evidence_refs: List[str] = Field(default_factory=list, max_length=200)
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
    evidence_refs: List[str] = Field(default_factory=list, max_length=200)
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
    evidence_refs: List[str] = Field(default_factory=list, max_length=200)
    confidence: float = Field(ge=0, le=1)
    warnings: List[str] = Field(default_factory=list, max_length=20)
