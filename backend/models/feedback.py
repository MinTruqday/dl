from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from uuid6 import uuid7

class TypoReportRequest(BaseModel):
    document_id: Optional[str] = None
    chapter_id: Optional[str] = None
    chapter_slug: Optional[str] = None
    selected_text: Optional[str] = None
    text_excerpt: Optional[str] = None
    suggested_text: Optional[str] = None
    context_text: Optional[str] = None
    description: Optional[str] = None

class ReportRequest(BaseModel):
    target_id: Optional[str] = None
    target_type: Optional[str] = None
    item_id: Optional[str] = None
    item_type: Optional[str] = None
    reason: str
    details: Optional[str] = None
    description: Optional[str] = None

class FeedbackInDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    user_id: str
    type: str
    data: dict
    status: str = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ResolveReportRequest(BaseModel):
    action: str
