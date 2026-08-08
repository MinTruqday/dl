from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class RetrieveRequest(BaseModel):
    query: str = Field(description="Nội dung truy vấn")
    document_ids: Optional[List[str]] = Field(default=None, description="Danh sách ID tài liệu giới hạn phạm vi tìm kiếm")
    k: int = Field(default=5, ge=1, le=100, description="Số lượng kết quả tối đa cần lấy")
    query_vector_override: Optional[List[float]] = Field(default=None, description="Vector truy vấn ghi đè nếu có")

class MultiQueryRetrieveRequest(BaseModel):
    question: str = Field(description="Câu hỏi truy vấn đa chiều")
    document_ids: Optional[List[str]] = Field(default=None, description="Danh sách ID tài liệu")
    k: int = Field(default=5, ge=1, le=100, description="Số lượng kết quả tối đa cần lấy")

class CrossDocRetrieveRequest(BaseModel):
    question: str = Field(description="Câu hỏi truy vấn liên tài liệu")
    document_ids: List[str] = Field(description="Danh sách ID các tài liệu cần phân tích so sánh")
    k: int = Field(default=5, ge=1, le=100, description="Số lượng kết quả tối đa cần lấy")

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
