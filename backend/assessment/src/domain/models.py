from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


def utc_now():
    return datetime.now(timezone.utc)


def empty_doc():
    return {"type": "doc", "content": []}


def normalize_response_value(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return [normalized for item in value if (normalized := normalize_response_value(item)) not in (None, "", [], {})]
    if isinstance(value, dict):
        return {
            key: normalized
            for key, item in value.items()
            if (normalized := normalize_response_value(item)) not in (None, "", [], {})
        }
    return value


class Persona(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"


class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    MATCHING = "matching"
    ORDERING = "ordering"
    NUMERIC = "numeric"
    SYMBOLIC_MATH = "symbolic_math"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"


class EducationProfileInput(BaseModel):
    personas: set[Persona]

    @field_validator("personas")
    @classmethod
    def validate_personas(cls, value):
        if not value:
            raise ValueError("Cần ít nhất một persona")
        return value


class UserSettingsInput(BaseModel):
    ui_language: Literal["vi", "en"] = "vi"
    theme: Literal["system", "light", "dark"] = "system"
    notifications_enabled: bool = True
    accessibility_preferences: dict[str, bool] = Field(default_factory=dict)
    default_subject: str | None = Field(default=None, max_length=100)
    privacy_mode: bool = False
    data_export_format: Literal["json", "csv"] = "json"


class TeacherProfileInput(BaseModel):
    explicit_preferences: dict[str, Any] = Field(default_factory=dict)
    use_own_materials: bool = True


class TeacherProfileEventInput(BaseModel):
    event_type: Literal["generation_accepted", "generation_rejected", "manual_edit", "question_type_selected", "difficulty_targeted", "material_used"]
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=8, max_length=200)


class CurriculumNodeInput(BaseModel):
    id: str | None = None
    node_type: Literal["education_level", "subject", "program", "chapter", "lesson", "section", "concept", "skill", "learning_objective"]
    parent_id: str | None = None
    education_level: str
    subject: str
    target_program: str
    title: str
    canonical_code: str
    curriculum_version: str


class CurriculumNodePatch(BaseModel):
    expected_revision: int = Field(ge=1)
    parent_id: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)
    canonical_code: str | None = Field(default=None, min_length=1, max_length=300)
    curriculum_version: str | None = Field(default=None, min_length=1, max_length=100)
    status: Literal["active", "obsolete"] | None = None


class CurriculumMergeInput(BaseModel):
    source_node_ids: list[str] = Field(min_length=1, max_length=100)
    expected_target_revision: int = Field(ge=1)
    expected_source_revisions: dict[str, int]

    @model_validator(mode="after")
    def validate_sources(self):
        if len(self.source_node_ids) != len(set(self.source_node_ids)):
            raise ValueError("Curriculum source node không được trùng")
        if set(self.source_node_ids) != set(self.expected_source_revisions):
            raise ValueError("Thiếu revision của curriculum source node")
        return self


class CurriculumSplitPart(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    canonical_code: str = Field(min_length=1, max_length=300)
    node_type: Literal["education_level", "subject", "program", "chapter", "lesson", "section", "concept", "skill", "learning_objective"] | None = None


class CurriculumSplitInput(BaseModel):
    expected_revision: int = Field(ge=1)
    parts: list[CurriculumSplitPart] = Field(min_length=2, max_length=20)

    @field_validator("parts")
    @classmethod
    def validate_parts(cls, value):
        codes = [part.canonical_code for part in value]
        if len(codes) != len(set(codes)):
            raise ValueError("Canonical code sau khi tách không được trùng")
        return value


class SourceObsoleteInput(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class SourceMappingInput(BaseModel):
    document_id: str
    chunk_id: str
    curriculum_node_ids: list[str] = Field(default_factory=list)
    concept_ids: list[str] = Field(default_factory=list)
    skill_ids: list[str] = Field(default_factory=list)
    source_type: Literal["curriculum", "teacher_material"]
    authority: Literal["official", "verified", "supplementary"]
    mapping_confidence: float = Field(ge=0, le=1)
    mapping_status: Literal["auto", "confirmed", "needs_review"] = "auto"
    source_version: str


class SourceMappingReviewInput(BaseModel):
    mapping_status: Literal["confirmed", "needs_review", "rejected"]
    mapping_confidence: float | None = Field(default=None, ge=0, le=1)
    curriculum_node_ids: list[str] | None = None
    concept_ids: list[str] | None = None
    skill_ids: list[str] | None = None


class OptionInput(BaseModel):
    id: str
    content_doc: dict[str, Any] = Field(default_factory=empty_doc)


class QuestionDraftCreate(BaseModel):
    question_type: QuestionType
    authoring_source: Literal["manual_tiptap", "import", "ai_generated", "hybrid"]
    stem_doc: dict[str, Any] = Field(default_factory=empty_doc)
    options: list[OptionInput] = Field(default_factory=list)
    answer_key: dict[str, Any] = Field(default_factory=dict)
    solution_doc: dict[str, Any] = Field(default_factory=empty_doc)
    scoring_rule: dict[str, Any] = Field(default_factory=dict)
    curriculum_links: list[dict[str, Any]] = Field(default_factory=list)
    concept_ids: list[str] = Field(default_factory=list)
    skill_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list, max_length=100)
    cognitive_level: str | None = None
    construct_data: dict[str, Any] = Field(default_factory=dict, alias="construct")
    source_evidence: list[dict[str, Any]] = Field(default_factory=list)
    source_page: int | None = None
    parse_confidence: float | None = Field(default=None, ge=0, le=1)
    locked: bool = False

    @field_validator("stem_doc", "solution_doc")
    @classmethod
    def validate_tiptap_doc(cls, value):
        if value.get("type") != "doc" or not isinstance(value.get("content", []), list):
            raise ValueError("Tiptap JSON không hợp lệ")
        return value


class QuestionDraftPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    question_type: QuestionType | None = None
    stem_doc: dict[str, Any] | None = None
    options: list[OptionInput] | None = None
    answer_key: dict[str, Any] | None = None
    solution_doc: dict[str, Any] | None = None
    scoring_rule: dict[str, Any] | None = None
    curriculum_links: list[dict[str, Any]] | None = None
    concept_ids: list[str] | None = None
    skill_ids: list[str] | None = None
    tags: list[str] | None = Field(default=None, max_length=100)
    cognitive_level: str | None = None
    construct_data: dict[str, Any] | None = Field(default=None, alias="construct")
    source_evidence: list[dict[str, Any]] | None = None
    locked: bool | None = None


class AssessmentDraftCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    context: dict[str, Any]
    layout_doc: dict[str, Any] = Field(default_factory=empty_doc)
    research_blind_mode: bool = False

    @field_validator("layout_doc")
    @classmethod
    def validate_layout(cls, value):
        if value.get("type") != "doc" or not isinstance(value.get("content", []), list):
            raise ValueError("Tiptap JSON không hợp lệ")
        return value


class AssessmentDraftPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=300)
    context: dict[str, Any] | None = None
    layout_doc: dict[str, Any] | None = None
    question_order: list[str] | None = None
    blueprint_id: str | None = None
    status: Literal["draft", "review", "ready"] | None = None


class CoverageConstraint(BaseModel):
    dimension: Literal["concept", "skill", "curriculum_node"]
    ids: list[str] = Field(min_length=1, max_length=200)
    minimum_count: int = Field(default=1, ge=0, le=500)
    required: bool = True


class BlueprintInput(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    total_questions: int = Field(gt=0, le=500)
    difficulty_distribution: dict[str, int]
    coverage_constraints: list[CoverageConstraint] = Field(default_factory=list)
    question_type_constraints: dict[str, int] = Field(default_factory=dict)
    cognitive_level_constraints: dict[str, int] = Field(default_factory=dict)
    target_learner: dict[str, Any] = Field(default_factory=dict)
    duration_minutes: int = Field(gt=0, le=1440)
    assessment_purpose: str = Field(default="assigned_assessment", min_length=1, max_length=100)
    total_points: float | None = Field(default=None, gt=0, le=10000)
    maximum_exposure_count: int | None = Field(default=None, ge=0)
    is_template: bool = False

    @field_validator("difficulty_distribution")
    @classmethod
    def validate_levels(cls, value):
        if set(value) != {"1", "2", "3", "4", "5"}:
            raise ValueError("Phân bố phải có đủ năm mức")
        if any(count < 0 for count in value.values()):
            raise ValueError("Số lượng câu không được âm")
        return value


class BlueprintPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    total_questions: int | None = Field(default=None, gt=0, le=500)
    difficulty_distribution: dict[str, int] | None = None
    coverage_constraints: list[CoverageConstraint] | None = None
    question_type_constraints: dict[str, int] | None = None
    cognitive_level_constraints: dict[str, int] | None = None
    target_learner: dict[str, Any] | None = None
    duration_minutes: int | None = Field(default=None, gt=0, le=1440)
    assessment_purpose: str | None = Field(default=None, min_length=1, max_length=100)
    total_points: float | None = Field(default=None, gt=0, le=10000)
    maximum_exposure_count: int | None = Field(default=None, ge=0)
    is_template: bool | None = None

    @field_validator("difficulty_distribution")
    @classmethod
    def validate_levels(cls, value):
        if value is not None and set(value) != {"1", "2", "3", "4", "5"}:
            raise ValueError("Phân bố phải có đủ năm mức")
        if value is not None and any(count < 0 for count in value.values()):
            raise ValueError("Số lượng câu không được âm")
        return value


class BlueprintSuggestionInput(BaseModel):
    total_questions: int = Field(gt=0, le=500)
    current_distribution: dict[str, int]

    @field_validator("current_distribution")
    @classmethod
    def validate_current_distribution(cls, value):
        if not set(value).issubset({"1", "2", "3", "4", "5"}):
            raise ValueError("Mức độ khó không hợp lệ")
        if any(count < 0 for count in value.values()):
            raise ValueError("Số lượng câu không được âm")
        return value


class AssessmentRebalanceInput(BaseModel):
    expected_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)


class LearnerFitInput(BaseModel):
    target_learner: dict[str, Any] = Field(default_factory=dict)
    target_success_range: list[float] = Field(default_factory=lambda: [0.45, 0.8], min_length=2, max_length=2)

    @model_validator(mode="after")
    def validate_fit_target(self):
        band = self.target_learner.get("ability_band")
        if band is not None and (
            not isinstance(band, list)
            or len(band) != 2
            or not all(isinstance(value, (int, float)) for value in band)
            or not 1 <= float(band[0]) <= float(band[1]) <= 5
        ):
            raise ValueError("Dải năng lực mục tiêu không hợp lệ")
        if not 0 < self.target_success_range[0] < self.target_success_range[1] < 1:
            raise ValueError("Dải xác suất thành công mục tiêu không hợp lệ")
        confidence = self.target_learner.get("confidence")
        if confidence is not None and (not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1):
            raise ValueError("Độ tin cậy người học không hợp lệ")
        return self


class ImportedPage(BaseModel):
    page_number: int = Field(ge=1)
    text: str = ""
    image_refs: list[dict[str, Any]] = Field(default_factory=list)
    formula_refs: list[dict[str, Any]] = Field(default_factory=list)


class ImportRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    document_id: str = Field(min_length=1, max_length=200)
    file_name: str = Field(min_length=1, max_length=500)
    pages: list[ImportedPage] = Field(min_length=1)
    answer_key: dict[str, Any] = Field(default_factory=dict)
    parser_version: str = "question_parser_v1"


class ImportFileRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    file_name: str = Field(min_length=1, max_length=500)
    data: str = Field(min_length=1, max_length=35_000_000)
    answer_key: dict[str, Any] = Field(default_factory=dict)


class ImportConfirmInput(BaseModel):
    selected_candidate_ids: list[str] = Field(default_factory=list)
    corrected_questions: dict[str, QuestionDraftCreate] = Field(default_factory=dict)


class GenerateRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    education_level: str
    target_program: str
    subject: str
    topic: str
    chapter_id: str | None = None
    lesson_id: str | None = None
    concept_ids: list[str] = Field(default_factory=list)
    skill_ids: list[str] = Field(default_factory=list)
    question_type: QuestionType = QuestionType.SINGLE_CHOICE
    count: int = Field(default=1, ge=1, le=50)
    target_difficulty: float | None = Field(default=None, ge=1, le=5)
    difficulty_distribution: dict[str, int] = Field(default_factory=dict)
    cognitive_level: str | None = None
    intended_purpose: str = "assessment"
    time_constraint_minutes: int | None = Field(default=None, gt=0)
    target_learner_band: dict[str, Any] = Field(default_factory=dict)
    use_teacher_materials: bool = False
    source_scope: Literal["curriculum_only", "curriculum_and_owned_material"] = "curriculum_only"
    source_evidence: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_generation_distribution(self):
        if self.difficulty_distribution:
            if set(self.difficulty_distribution) != {"1", "2", "3", "4", "5"}:
                raise ValueError("Phân bố sinh câu phải có đủ năm mức")
            if any(value < 0 for value in self.difficulty_distribution.values()):
                raise ValueError("Phân bố sinh câu không được âm")
            if sum(self.difficulty_distribution.values()) != self.count:
                raise ValueError("Tổng phân bố sinh câu phải bằng số câu")
        return self


class DraftAiActionInput(BaseModel):
    action: Literal["clarify_wording", "increase_difficulty", "decrease_difficulty", "regenerate_distractors", "regenerate_item", "change_question_type"]
    instruction: str = ""


class DistractorRevisionInput(BaseModel):
    replacements: dict[str, str] = Field(min_length=1)


class ReviewDecisionInput(BaseModel):
    reviewer_note: str = ""


class ValidityReviewInput(BaseModel):
    status: Literal["approved", "rejected"]
    risk_flags: list[Literal["language_bias", "cultural_context", "accessibility", "construct_irrelevant_context", "differential_opportunity"]] = Field(default_factory=list)
    reviewer_note: str = Field(min_length=1, max_length=2000)


class QuestionBankAddInput(BaseModel):
    assessment_draft_id: str
    question_ids: list[str] = Field(min_length=1, max_length=500)

    @field_validator("question_ids")
    @classmethod
    def validate_unique_question_ids(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Danh sách câu hỏi không được trùng")
        return value


class QuestionArchiveInput(BaseModel):
    reason: str = Field(default="", max_length=1000)


class AssignmentInput(BaseModel):
    student_ids: list[str] = Field(min_length=1)
    available_from: datetime | None = None
    due_at: datetime | None = None
    idempotency_key: str = Field(min_length=8, max_length=200)

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.available_from and self.due_at and self.due_at <= self.available_from:
            raise ValueError("Hạn nộp phải sau thời điểm mở bài")
        return self


class CalibrationRunInput(BaseModel):
    question_version_ids: list[str] = Field(default_factory=list)
    population_context: dict[str, Any] = Field(default_factory=dict)
    method: Literal["CTT", "Rasch"] = "CTT"
    evidence_policy_version: str = "evidence_v1"
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class CalibrationJobInput(CalibrationRunInput):
    callback_requested: bool = False


class PrivacyPurgeInput(BaseModel):
    older_than_days: int = Field(ge=30, le=3650)


class TeacherEstimateInput(BaseModel):
    estimated_difficulty: float = Field(ge=1, le=5)
    self_confidence: Literal["low", "medium", "high"] | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class DifficultyPredictionInput(BaseModel):
    model_version: str = Field(default="cold_start_v1", min_length=1, max_length=200, pattern=r"^[A-Za-z0-9._:-]+$")
    prediction_kind: Literal["structured", "llm_direct"] = "structured"


class DifficultyTargetInput(BaseModel):
    target_difficulty: float = Field(ge=1, le=5)
    blueprint_id: str | None = None


class AttemptCreate(BaseModel):
    attempt_number: int = Field(default=1, ge=1)
    assignment_id: str | None = None
    idempotency_key: str = Field(min_length=8, max_length=200)


class AssessmentCreate(BaseModel):
    assessment_draft_id: str
    delivery_policy: dict[str, Any] = Field(default_factory=dict)


class PublishInput(BaseModel):
    assessment_draft_id: str
    expected_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)
    scheduled_for: datetime | None = None

    @field_validator("scheduled_for")
    @classmethod
    def validate_scheduled_for(cls, value):
        if value is not None and value.tzinfo is None:
            raise ValueError("Thời điểm xuất bản phải có múi giờ")
        return value


class AssessmentCloneInput(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)


class AssessmentArchiveInput(BaseModel):
    reason: str = Field(default="", max_length=1000)


class AssessmentUnpublishInput(BaseModel):
    reason: str = Field(default="", max_length=1000)


class ResponseInput(BaseModel):
    question_version_id: str
    answer: dict[str, Any]
    response_sequence: int = Field(ge=1)
    client_revision: int = Field(default=1, ge=1)
    response_time_ms: int = Field(ge=0)
    answer_change_count: int = Field(default=0, ge=0)
    is_first_exposure: bool = True
    exposure_index: int = Field(default=1, ge=1)
    hint_used: bool = False
    explanation_seen_before_answer: bool = False
    delivery_context: Literal["assigned", "diagnostic", "practice"] = "assigned"
    technical_flags: list[str] = Field(default_factory=list)
    flag_for_review: bool = False
    idempotency_key: str = Field(min_length=8, max_length=200)

    @field_validator("answer")
    @classmethod
    def normalize_answer(cls, value):
        return normalize_response_value(value)


class RevisionProposalInput(BaseModel):
    target_difficulty: float = Field(ge=1, le=5)
    proposed_version: dict[str, Any]
    reason_codes: list[str]
    evidence_ids: list[str] = Field(default_factory=list)
    construct_check: dict[str, Any]

    @model_validator(mode="after")
    def require_construct_check(self):
        if "passed" not in self.construct_check:
            raise ValueError("Thiếu kết quả kiểm tra construct")
        return self
