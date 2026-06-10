from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid

class AITextRequest(BaseModel):
    text: str
    action: str
    context: Optional[str] = ""
    target_lang: Optional[str] = "Vietnamese"



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
