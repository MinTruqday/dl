from typing import Annotated, Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

class GenerationRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=100000, description="<input_context>The exact user request to be processed by Metis.</input_context>")
    max_tokens: int = Field(default=500, ge=1, le=4000, description="<constraints>Maximum token limit. Metis must enforce this strictly to prevent overflow.</constraints>")
    temperature: float = Field(default=0.3, ge=0, le=1, description="<constraints>Temperature controls randomness. Keep low (0.0-0.3) for logic, higher (0.7) for creativity.</constraints>")

class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>The source text requiring translation.</input_context>")
    target_lang: str = Field(min_length=2, max_length=32, description="<constraints>The target ISO language code. Metis must translate with native fluency.</constraints>")

class CodeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=50000, description="<input_context>The coding task specification.</input_context>")
    language: str = Field(default="python", min_length=1, max_length=32, description="<constraints>The target programming language. Must follow idiomatic standards.</constraints>")

class GrammarRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Source text to check or transform.</input_context>")

class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200000, description="<input_context>Source text that must be summarized without losing material facts.</input_context>")
    language: str = Field(default="auto", min_length=2, max_length=32, description="<constraints>Output language or auto to follow the source language.</constraints>")

class ActionRequest(BaseModel):
    action: str = Field(min_length=1, max_length=64, description="<critical_instructions>Supported editor action to execute.</critical_instructions>")
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Selected editor text affected by the action.</input_context>")
    context: Optional[str] = Field(default="", max_length=100000, description="<input_context>Optional surrounding document context for accurate transformation.</input_context>")

class CitationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Claims or content requiring supporting citations.</input_context>")
    style: str = Field(default="APA", min_length=1, max_length=32, description="<constraints>Required citation formatting style such as APA or MLA.</constraints>")

class ToneRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Source text whose tone must be transformed.</input_context>")
    tone: str = Field(min_length=1, max_length=64, description="<constraints>Target tone to apply while preserving meaning.</constraints>")
    expansion: bool = Field(default=False, description="<constraints>Whether the transformation may expand the source content.</constraints>")

class ReviewRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Content to evaluate in the peer review workflow.</input_context>")
    criteria: Optional[List[Annotated[str, Field(min_length=1, max_length=200)]]] = Field(default=None, max_length=20, description="<constraints>Optional explicit review criteria applied to the content.</constraints>")

class SynthesisRequest(BaseModel):
    document_ids: List[Annotated[str, Field(min_length=1, max_length=128)]] = Field(min_length=1, max_length=100, description="<input_context>Authorized document identifiers used as synthesis evidence.</input_context>")
    query: str = Field(min_length=1, max_length=20000, description="<input_context>Question or synthesis objective applied to the selected documents.</input_context>")

class PlagiarismCheckRequest(BaseModel):
    content: str = Field(min_length=1, max_length=100000, description="<input_context>Content whose overlap and attribution risk must be assessed.</input_context>")

class CoverGenerateRequest(BaseModel):
    style: str = Field(default="minimalist", min_length=1, max_length=100, description="<constraints>Visual style requested for cover generation.</constraints>")

class AISuggestionRequest(BaseModel):
    context: str = Field(min_length=1, max_length=100000, description="<input_context>Document context used to generate relevant suggestions.</input_context>")

class GlossaryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200000, description="<input_context>Source text from which domain terms and definitions are extracted.</input_context>")

class StyleImitationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Content to rewrite while preserving its factual meaning.</input_context>")
    style_sample: str = Field(min_length=1, max_length=50000, description="<input_context>Reference sample defining the target writing characteristics.</input_context>")
    target_length: Optional[int] = Field(default=None, ge=1, le=4000, description="<constraints>Optional target output length in tokens.</constraints>")

class DraftWithMemoryRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=100000, description="<input_context>Drafting objective augmented with authenticated user memory.</input_context>")

class ExtractToStorageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200000, description="<input_context>Source content from which artifacts must be extracted.</input_context>")
    extraction_goals: List[Annotated[str, Field(min_length=1, max_length=500)]] = Field(min_length=1, max_length=20, description="<constraints>Explicit artifact extraction objectives.</constraints>")

class WebFactCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Claims to verify against current web evidence.</input_context>")

class ComplianceScreenRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Content to evaluate against configured compliance policy.</input_context>")

class SemanticDiffRequest(BaseModel):
    text1: str = Field(min_length=1, max_length=100000, description="<input_context>Original text used as the semantic comparison baseline.</input_context>")
    text2: str = Field(min_length=1, max_length=100000, description="<input_context>Revised text compared with the semantic baseline.</input_context>")

class MemoryUserEditsRequest(BaseModel):
    action: str = Field(min_length=1, max_length=32, description="<critical_instructions>Supported memory mutation action.</critical_instructions>")
    content: str = Field(min_length=1, max_length=10000, description="<input_context>Memory content supplied by the authenticated user.</input_context>")
    memory_id: Optional[str] = Field(default=None, min_length=1, max_length=128, description="<input_context>Owned memory identifier required by update and delete actions.</input_context>")

class QuickRepliesRequest(BaseModel):
    history_messages: List[Annotated[str, Field(min_length=1, max_length=10000)]] = Field(min_length=1, max_length=50, description="<input_context>Recent bounded conversation messages used to generate replies.</input_context>")

class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000, description="<input_context>Search query embedded against the authorized document index</input_context>")
    limit: int = Field(default=20, ge=1, le=30, description="<constraints>Maximum distinct document results</constraints>")

class RetrievalExpansionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000, description="<input_context>Question to expand for semantic retrieval</input_context>")

class CrossDocumentExpansionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000, description="<input_context>Question to decompose across documents</input_context>")
    document_ids: List[Annotated[str, Field(min_length=1, max_length=128)]] = Field(min_length=2, max_length=100, description="<input_context>Ordered document identifiers receiving one retrieval query each</input_context>")

class RagChunkSafetyRequest(BaseModel):
    texts: List[Annotated[str, Field(min_length=1, max_length=4000)]] = Field(min_length=1, max_length=500, description="<input_context>Bounded retrieval chunks requiring security classification</input_context>")

class RagDocumentSummaryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=15000, description="<input_context>Bounded leading document content requiring a retrieval summary</input_context>")

class StructuredInferenceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

class AssessmentQuestionGenerationRequest(BaseModel):
    education_level: str = Field(min_length=1, max_length=100, description="<constraints>Cấp học của câu hỏi</constraints>")
    target_program: str = Field(min_length=1, max_length=100, description="<constraints>Chương trình đích</constraints>")
    subject: str = Field(min_length=1, max_length=100, description="<constraints>Môn học đích</constraints>")
    topic: str = Field(min_length=1, max_length=500, description="<constraints>Chủ đề cần đánh giá</constraints>")
    question_type: Literal["single_choice", "multiple_choice", "true_false", "matching", "ordering", "numeric", "symbolic_math", "short_answer", "essay"] = Field(description="<constraints>Loại câu hỏi có cấu trúc</constraints>")
    target_difficulty: float = Field(ge=1, le=5, description="<constraints>Mức độ khó mục tiêu từ một đến năm</constraints>")
    cognitive_level: Optional[str] = Field(default=None, max_length=100, description="<constraints>Mức nhận thức tùy chọn</constraints>")
    evidence: List[dict[str, Any]] = Field(min_length=1, max_length=20, description="<input_context>Bằng chứng RAG đã kiểm soát quyền và provenance</input_context>")

class GeneratedQuestionOption(StructuredInferenceResult):
    id: str = Field(min_length=1, max_length=20, description="<output_format>Mã phương án ổn định</output_format>")
    text: str = Field(min_length=1, max_length=2000, description="<output_format>Nội dung phương án</output_format>")

class GeneratedAssessmentQuestion(StructuredInferenceResult):
    stem: str = Field(min_length=1, max_length=5000, description="<output_format>Nội dung câu hỏi không chứa đáp án</output_format>")
    options: List[GeneratedQuestionOption] = Field(default_factory=list, max_length=12, description="<output_format>Các phương án có cấu trúc nếu loại câu yêu cầu</output_format>")
    answer_key: dict[str, Any] = Field(description="<output_format>Đáp án theo schema của loại câu hỏi</output_format>")
    solution: str = Field(min_length=1, max_length=5000, description="<output_format>Lời giải dựa trên bằng chứng</output_format>")
    primary_concept: str = Field(min_length=1, max_length=500, description="<output_format>Khái niệm chính được đo</output_format>")
    primary_skill: str = Field(min_length=1, max_length=500, description="<output_format>Kỹ năng chính được đo</output_format>")
    learning_objective: str = Field(min_length=1, max_length=1000, description="<output_format>Mục tiêu học tập được đo</output_format>")

class DirectDifficultyJudgmentRequest(BaseModel):
    question_type: str = Field(min_length=1, max_length=100, description="<input_context>Loại câu hỏi cần đánh giá trực tiếp</input_context>")
    stem: str = Field(min_length=1, max_length=10000, description="<input_context>Nội dung câu hỏi cần đánh giá trực tiếp</input_context>")
    options: list[str] = Field(default_factory=list, max_length=20, description="<input_context>Các phương án trả lời nếu có</input_context>")
    answer_key: dict[str, Any] = Field(default_factory=dict, description="<input_context>Đáp án có cấu trúc của câu hỏi</input_context>")
    solution: str = Field(default="", max_length=10000, description="<input_context>Lời giải của câu hỏi nếu có</input_context>")
    education_level: str = Field(default="", max_length=100, description="<input_context>Cấp học của câu hỏi</input_context>")
    subject: str = Field(default="", max_length=100, description="<input_context>Môn học của câu hỏi</input_context>")
    target_program: str = Field(default="", max_length=100, description="<input_context>Chương trình đích của câu hỏi</input_context>")

class DirectDifficultyJudgment(StructuredInferenceResult):
    predicted_difficulty: float = Field(ge=1, le=5, description="<output_format>Độ khó dự đoán trực tiếp từ một đến năm</output_format>")
    confidence: float = Field(ge=0, le=1, description="<output_format>Độ tin cậy của dự đoán trực tiếp</output_format>")
    reason_summary: list[str] = Field(min_length=1, max_length=8, description="<output_format>Các lý do ngắn giải thích mức độ khó</output_format>")

class QuickRepliesOutput(StructuredInferenceResult):
    replies: list[str] = Field(min_length=3, max_length=3, description="<output_format>Exactly three concise reply suggestions.</output_format>")

    @field_validator("replies")
    @classmethod
    def validate_replies(cls, replies):
        for reply in replies:
            if not isinstance(reply, str) or not 1 <= len(reply.split()) <= 6:
                raise ValueError("Each reply must contain one to six words")
            if "." * 3 in reply or chr(8230) in reply:
                raise ValueError("Ellipses are not allowed")
            if any(ord(char) >= 0x1F000 for char in reply):
                raise ValueError("Pictographs are not allowed")
        return replies

class PlagiarismResult(StructuredInferenceResult):
    plagiarism_score: float = Field(ge=0, le=1, description="<output_format>Normalized plagiarism risk score.</output_format>")
    status: str = Field(pattern=r"^(clean|warning|danger)$", description="<output_format>Severity derived from the normalized score.</output_format>")
    message: str = Field(min_length=1, max_length=2000, description="<output_format>Concise evidence based assessment.</output_format>")
    matched_sources: list[str] = Field(default_factory=list, max_length=20, description="<output_format>Identifiers of sources supporting the assessment.</output_format>")

class DocumentAnalysisRequest(BaseModel):
    context: str = Field(min_length=1, max_length=200000, description="<input_context>Extracted document text to analyze.</input_context>")
    ext: str = Field(default="txt", pattern=r"^[a-zA-Z0-9]{1,16}$", description="<constraints>Filename extension without a leading dot.</constraints>")
    folder_str: str = Field(default="NONE", max_length=10000, description="<input_context>Bounded folder options available for classification.</input_context>")

class ExtractTextRequest(BaseModel):
    document_id: str = Field(min_length=1, max_length=128, description="<critical_instructions>Authorized document whose stored file content will be extracted.</critical_instructions>")

class DocumentEntities(StructuredInferenceResult):
    people: list[str] = Field(default_factory=list, max_length=100, description="<output_format>People explicitly identified in the supplied document.</output_format>")
    organizations: list[str] = Field(default_factory=list, max_length=100, description="<output_format>Organizations explicitly identified in the supplied document.</output_format>")
    dates: list[str] = Field(default_factory=list, max_length=100, description="<output_format>Dates explicitly identified in the supplied document.</output_format>")
    amounts: list[str] = Field(default_factory=list, max_length=100, description="<output_format>Monetary amounts explicitly identified in the supplied document.</output_format>")

class DocumentAnalysisResult(StructuredInferenceResult):
    summary: str = Field(min_length=1, max_length=5000, description="<output_format>Grounded document summary.</output_format>")
    suggested_name: str = Field(min_length=1, max_length=300, description="<output_format>Safe descriptive filename.</output_format>")
    tags: list[str] = Field(min_length=1, max_length=20, description="<output_format>Relevant search tags.</output_format>")
    entities: DocumentEntities = Field(description="<output_format>Grounded named entities grouped by category.</output_format>")
    is_safe: bool = Field(description="<output_format>Whether the supplied content is safe to process.</output_format>")
    target_folder_id: str = Field(min_length=1, max_length=128, description="<output_format>Identifier of the best matching supplied folder or NONE.</output_format>")

class GlossaryEntry(StructuredInferenceResult):
    term: str = Field(min_length=1, max_length=300, description="<output_format>Technical term found in the source text.</output_format>")
    definition: str = Field(min_length=1, max_length=2000, description="<output_format>Grounded definition derived from the source text.</output_format>")

class GlossaryResult(StructuredInferenceResult):
    glossary: list[GlossaryEntry] = Field(default_factory=list, max_length=15, description="<output_format>Deduplicated glossary entries grounded in the source text.</output_format>")

class ExtractedArtifact(StructuredInferenceResult):
    goal: str = Field(min_length=1, max_length=500, description="<output_format>Extraction goal satisfied by this artifact.</output_format>")
    value: str = Field(min_length=1, max_length=10000, description="<output_format>Artifact value grounded in the supplied source.</output_format>")
    evidence: str = Field(default="", max_length=2000, description="<output_format>Concise source evidence supporting the artifact.</output_format>")

class ArtifactExtractionResult(StructuredInferenceResult):
    artifacts: list[ExtractedArtifact] = Field(default_factory=list, max_length=20, description="<output_format>Artifacts matched to the requested extraction goals.</output_format>")
