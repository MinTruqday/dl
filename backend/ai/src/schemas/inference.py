from typing import Annotated, Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class RetrievalExpansionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000, description="Câu hỏi cần mở rộng cho truy xuất ngữ nghĩa")


class CrossDocumentExpansionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000, description="Câu hỏi cần phân rã theo từng tài liệu")
    document_ids: List[Annotated[str, Field(min_length=1, max_length=128)]] = Field(
        min_length=2,
        max_length=100,
        description="Danh sách tài liệu theo thứ tự cần truy xuất",
    )


class RagChunkSafetyRequest(BaseModel):
    texts: List[Annotated[str, Field(min_length=1, max_length=4000)]] = Field(
        min_length=1,
        max_length=500,
        description="Các đoạn truy xuất cần kiểm tra an toàn",
    )


class RagDocumentSummaryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=15000, description="Nội dung tài liệu cần tóm tắt cho RAG")


class StructuredInferenceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AssessmentQuestionGenerationRequest(BaseModel):
    education_level: str = Field(min_length=1, max_length=100, description="Cấp học của câu hỏi")
    target_program: str = Field(min_length=1, max_length=100, description="Chương trình giáo dục đích")
    subject: str = Field(min_length=1, max_length=100, description="Môn học đích")
    topic: str = Field(min_length=1, max_length=500, description="Chủ đề cần đánh giá")
    question_type: Literal[
        "single_choice",
        "multiple_choice",
        "true_false",
        "matching",
        "ordering",
        "numeric",
        "symbolic_math",
        "short_answer",
        "essay",
    ] = Field(description="Loại câu hỏi có cấu trúc")
    target_difficulty: float = Field(ge=1, le=5, description="Độ khó mục tiêu từ một đến năm")
    cognitive_level: Optional[str] = Field(default=None, max_length=100, description="Mức nhận thức tùy chọn")
    evidence: List[dict[str, Any]] = Field(min_length=1, max_length=20, description="Bằng chứng RAG đã kiểm soát")


class GeneratedQuestionOption(StructuredInferenceResult):
    id: str = Field(min_length=1, max_length=20, description="Mã phương án ổn định")
    text: str = Field(min_length=1, max_length=2000, description="Nội dung phương án")


class GeneratedAssessmentQuestion(StructuredInferenceResult):
    stem: str = Field(min_length=1, max_length=5000, description="Nội dung câu hỏi")
    options: List[GeneratedQuestionOption] = Field(default_factory=list, max_length=12, description="Các phương án trả lời")
    answer_key: dict[str, Any] = Field(description="Đáp án có cấu trúc")
    solution: str = Field(min_length=1, max_length=5000, description="Lời giải dựa trên bằng chứng")
    primary_concept: str = Field(min_length=1, max_length=500, description="Khái niệm chính")
    primary_skill: str = Field(min_length=1, max_length=500, description="Kỹ năng chính")
    learning_objective: str = Field(min_length=1, max_length=1000, description="Mục tiêu học tập")


class DirectDifficultyJudgmentRequest(BaseModel):
    question_type: str = Field(min_length=1, max_length=100, description="Loại câu hỏi")
    stem: str = Field(min_length=1, max_length=10000, description="Nội dung câu hỏi")
    options: list[str] = Field(default_factory=list, max_length=20, description="Các phương án trả lời")
    answer_key: dict[str, Any] = Field(default_factory=dict, description="Đáp án có cấu trúc")
    solution: str = Field(default="", max_length=10000, description="Lời giải")
    education_level: str = Field(default="", max_length=100, description="Cấp học")
    subject: str = Field(default="", max_length=100, description="Môn học")
    target_program: str = Field(default="", max_length=100, description="Chương trình đích")


class DirectDifficultyJudgment(StructuredInferenceResult):
    predicted_difficulty: float = Field(ge=1, le=5, description="Độ khó dự đoán từ một đến năm")
    confidence: float = Field(ge=0, le=1, description="Độ tin cậy")
    reason_summary: list[str] = Field(min_length=1, max_length=8, description="Các lý do ngắn")
