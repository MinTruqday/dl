from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class RelationItem(BaseModel):
    source: str = Field(description="Tên thực thể nguồn")
    relation: str = Field(description="Quan hệ giữa hai thực thể")
    target: str = Field(description="Tên thực thể đích")
    document_id: str = Field(default="", description="ID tài liệu liên kết")

class GraphExpandRequest(BaseModel):
    document_ids: List[str] = Field(description="Danh sách ID tài liệu")
    seed_query: str = Field(description="Truy vấn hạt giống để tìm kiếm thực thể liên quan")
    limit: int = Field(default=20, ge=1, le=100, description="Giới hạn số quan hệ cần lấy")
    requester_id: Optional[str] = None
    is_admin: bool = False

class ReplaceDocumentGraphRequest(BaseModel):
    document_id: str = Field(description="ID tài liệu")
    relations: List[RelationItem] = Field(description="Danh sách các quan hệ thực thể")
    requester_id: Optional[str] = None
    is_admin: bool = False

class GraphExpandResponse(BaseModel):
    context: str = Field(description="Ngữ cảnh đồ thị đã được định dạng")
    relations: List[RelationItem] = Field(default_factory=list, description="Danh sách quan hệ chi tiết")
