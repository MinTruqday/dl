from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CurriculumFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    education_level: Optional[str] = None
    subject: Optional[str] = None
    target_program: Optional[str] = None
    chapter_id: Optional[str] = None
    lesson_id: Optional[str] = None
    section_id: Optional[str] = None
    concept_ids: Optional[List[str]] = None
    skill_ids: Optional[List[str]] = None
    learning_objective_ids: Optional[List[str]] = None
    content_type: Optional[str] = None
    source_type: Optional[str] = None
    authority: Optional[List[str]] = None
    source_version: Optional[str] = None

class RetrieveRequest(BaseModel):
    query: str = Field(description="Nội dung truy vấn")
    document_ids: Optional[List[str]] = Field(default=None, description="Danh sách ID tài liệu giới hạn phạm vi tìm kiếm")
    k: int = Field(default=5, ge=1, le=100, description="Số lượng kết quả tối đa cần lấy")
    query_vector_override: Optional[List[float]] = Field(default=None, description="Vector truy vấn ghi đè nếu có")
    requester_id: Optional[str] = None
    is_admin: bool = False
    metadata_filters: CurriculumFilters = Field(default_factory=CurriculumFilters)

class MultiQueryRetrieveRequest(BaseModel):
    question: str = Field(description="Câu hỏi truy vấn đa chiều")
    document_ids: Optional[List[str]] = Field(default=None, description="Danh sách ID tài liệu")
    k: int = Field(default=5, ge=1, le=100, description="Số lượng kết quả tối đa cần lấy")
    requester_id: Optional[str] = None
    is_admin: bool = False
    metadata_filters: CurriculumFilters = Field(default_factory=CurriculumFilters)

class CrossDocRetrieveRequest(BaseModel):
    question: str = Field(description="Câu hỏi truy vấn liên tài liệu")
    document_ids: List[str] = Field(description="Danh sách ID các tài liệu cần phân tích so sánh")
    k: int = Field(default=5, ge=1, le=100, description="Số lượng kết quả tối đa cần lấy")
    requester_id: Optional[str] = None
    is_admin: bool = False
    metadata_filters: CurriculumFilters = Field(default_factory=CurriculumFilters)

class RetrievedDocument(BaseModel):
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0

class CitationItem(BaseModel):
    chunk_id: str = ""
    document_id: str = ""
    title: str = ""
    chunk_index: Any = ""
    label: str = ""

class RetrieveResponse(BaseModel):
    documents: List[RetrievedDocument]
    citations: List[CitationItem] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
