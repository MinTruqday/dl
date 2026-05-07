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
    quality: int # 1-5
