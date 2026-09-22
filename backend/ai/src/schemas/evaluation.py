from typing import Literal

from pydantic import BaseModel, Field


class TaskEvaluation(BaseModel):
    status: Literal["PASS", "FAIL"] = Field(
        description="PASS khi kết quả đúng đủ có căn cứ và an toàn ngược lại là FAIL"
    )
    feedback: str = Field(
        description="Nhận xét cụ thể có căn cứ cho kết quả đánh giá"
    )
    revised_task: str = Field(
        default="",
        description="Task đã sửa khi trạng thái là FAIL và để trống khi trạng thái là PASS",
    )


class DocumentGrade(BaseModel):
    is_relevant: bool = Field(
        description="Đúng khi tài liệu chứa thông tin trực tiếp giải quyết truy vấn"
    )


class QualityEvaluation(BaseModel):
    relevance: float = Field(
        ge=0.0,
        le=1.0,
        description="Mức độ trả lời trực tiếp truy vấn từ 0 đến 1",
    )
    grounding: float = Field(
        ge=0.0,
        le=1.0,
        description="Mức độ được ngữ cảnh cung cấp hỗ trợ từ 0 đến 1",
    )
    completeness: float = Field(
        ge=0.0,
        le=1.0,
        description="Mức độ bao phủ các phần quan trọng của truy vấn từ 0 đến 1",
    )
    overall: float = Field(
        ge=0.0,
        le=1.0,
        description="Điểm chất lượng tổng hợp từ 0 đến 1",
    )
    should_retry: bool = Field(
        description="Đúng khi kết quả không an toàn thiếu căn cứ không đầy đủ hoặc dưới ngưỡng chất lượng"
    )
    feedback: str = Field(
        description="Nhận xét cụ thể về phần chưa đạt và cách sửa"
    )


class ErrorMessageJudgment(BaseModel):
    is_error_message: bool = Field(
        description="Đúng khi văn bản là lỗi hệ thống hoặc lỗi kỹ thuật thô"
    )
    reason: str = Field(
        description="Lý do ngắn gọn cho phân loại"
    )


class HallucinationJudgment(BaseModel):
    is_hallucination_or_refusal: bool = Field(
        description="Đúng khi kết quả từ chối hoặc chứa thông tin không được xác minh"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Độ tin cậy của đánh giá từ 0 đến 1",
    )
    explanation: str = Field(
        description="Giải thích cụ thể tuyên bố thiếu căn cứ hoặc lý do phát hiện từ chối"
    )


class RelevanceJudgment(BaseModel):
    is_relevant: bool = Field(
        description="Đúng khi kết quả trả lời trực tiếp ý định chính của truy vấn"
    )
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Điểm liên quan từ 0 đến 1",
    )
    feedback: str = Field(
        description="Nhận xét phần thiếu thiếu căn cứ hoặc phù hợp với truy vấn"
    )


class HallucinationGrade(BaseModel):
    is_refusal_or_hallucination: bool = Field(
        description="Đúng khi kết quả từ chối hoặc chứa thông tin không được xác minh"
    )
    reason: str = Field(
        description="Lý do ngắn gọn cho đánh giá"
    )


class JudgeScores(BaseModel):
    accuracy: int = Field(
        ge=0,
        le=10,
        description="Điểm chính xác từ 0 đến 10",
    )
    completeness: int = Field(
        ge=0, le=10, description="Điểm đầy đủ từ 0 đến 10"
    )
    relevance: int = Field(
        ge=0,
        le=10,
        description="Điểm liên quan từ 0 đến 10",
    )
    explanation: str = Field(
        min_length=1,
        max_length=2000,
        description="Căn cứ ngắn gọn cho các điểm đánh giá",
    )
