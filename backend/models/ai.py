from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid

class AITextRequest(BaseModel):
    text: str
    action: str
    context: Optional[str] = ""
    target_lang: Optional[str] = "Vietnamese"

class FlashcardRequest(BaseModel):
    text: str
    context: str = ""

class FlashcardReviewRequest(BaseModel):
    card_id: str
    quality: int

class AIMindmapRequest(BaseModel):
    text: str
    depth: int = 2

class AICitationRequest(BaseModel):
    text: str
    style: str = "APA"

class AIToneRequest(BaseModel):
    text: str
    tone: str
    expansion: bool = False

class AIReviewRequest(BaseModel):
    text: str
    criteria: Optional[List[str]] = None

class AISynthesisRequest(BaseModel):
    document_ids: List[str]
    query: str

class AIPostRequest(BaseModel):
    text: str
    context: Optional[str] = ""

class AIStoryRequest(BaseModel):
    text: str

class AIEngagementRequest(BaseModel):
    content: str
