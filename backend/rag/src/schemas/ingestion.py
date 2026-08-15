from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class IngestRequest(BaseModel):
    document_id: str = Field(description="Mã định danh duy nhất của tài liệu cần nạp")
    requester_id: Optional[str] = None
    is_admin: bool = False

class IngestResponse(BaseModel):
    document_id: str
    status: str
    chunks_count: int
    summary_generated: bool = False
    extraction_method: str = "local"


class AttachmentConversionRequest(BaseModel):
    data: str = Field(min_length=1, max_length=35_000_000)
    filename: str = Field(default="attachment.pdf", min_length=1, max_length=255)
