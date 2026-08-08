from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class IngestRequest(BaseModel):
    document_id: str = Field(description="Mã định danh duy nhất của tài liệu cần nạp")

class IngestResponse(BaseModel):
    document_id: str
    status: str
    chunks_count: int
    summary_generated: bool = False
    graph_entities_count: int = 0
    extraction_method: str = "local"
