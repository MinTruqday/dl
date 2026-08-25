from typing import Annotated, Any, List, Literal

from pydantic import BaseModel, ConfigDict, Field


class RetrievalExpansionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000, description="Câu hỏi cần mở rộng cho truy xuất ngữ nghĩa")


class CrossDocumentExpansionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000, description="Câu hỏi cần phân rã theo từng tài liệu")
    document_ids: List[Annotated[str, Field(min_length=1, max_length=128)]] = Field(min_length=2, max_length=100, description="Danh sách tài liệu theo thứ tự cần truy xuất")


class RagChunkSafetyRequest(BaseModel):
    texts: List[Annotated[str, Field(min_length=1, max_length=4000)]] = Field(min_length=1, max_length=500, description="Các đoạn truy xuất cần kiểm tra an toàn")


class RagDocumentSummaryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=15000, description="Nội dung tài liệu cần tóm tắt cho RAG")


class QAAssistanceRequest(BaseModel):
    capability: Literal["requirement_lint", "scenario_generation", "test_generation", "trace_recommendation", "semantic_change", "impact_analysis", "maintenance_proposal", "regression_recommendation", "defect_linking"] = Field(description="Năng lực QA cần thực hiện")
    project_id: str = Field(min_length=1, max_length=128, description="Mã Project giới hạn phạm vi xử lý")
    instruction: str = Field(default="", max_length=5000, description="Chỉ dẫn nghiệp vụ bổ sung của người dùng")
    evidence: List[dict[str, Any]] = Field(min_length=1, max_length=100, description="Bằng chứng artifact đã được giới hạn theo Project")


class QAAssistanceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: str = Field(description="Năng lực QA đã thực hiện")
    suggestions: List[dict[str, Any]] = Field(default_factory=list, max_length=100, description="Danh sách đề xuất chỉ ở trạng thái chờ duyệt")
    evidence_refs: List[str] = Field(default_factory=list, max_length=200, description="Mã bằng chứng hỗ trợ kết quả")
    confidence: float = Field(ge=0, le=1, description="Độ tin cậy tham khảo của mô hình")
    warnings: List[str] = Field(default_factory=list, max_length=50, description="Cảnh báo giới hạn và xung đột bằng chứng")
    status: Literal["SUCCESS", "DEGRADED"] = Field(default="SUCCESS", description="Trạng thái vận hành của năng lực AI")
    degraded_mode: str | None = Field(default=None, description="Chế độ fallback khi provider hoặc retrieval không sẵn sàng")
    model: dict[str, Any] = Field(default_factory=dict, description="Metadata version của model prompt và tool schema")
