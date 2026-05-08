from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class TypoReportRequest(BaseModel):
    document_id: str
    chapter_id: str
    selected_text: str
    suggested_text: Optional[str] = None
    context_text: Optional[str] = None

class ReportRequest(BaseModel):
    target_id: str
    target_type: str
    reason: str
    details: Optional[str] = None

class FeedbackInDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    type: str
    data: dict
    status: str = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ResolveReportRequest(BaseModel):
    action: str
