from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid
from uuid6 import uuid7

class ChapterBase(BaseModel):
    title: str
    content: str
    order: int = 0
    is_premium: bool = False
    price_dl: int = 0
    words_count: int = 0
    locked: bool = False
    readability_score: float = 0.0
    vocabulary_richness: float = 0.0
    level: int = 0

class ChapterCreate(ChapterBase):
    pass

class ChapterInDB(ChapterBase):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    document_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChapterResponse(ChapterBase):
    id: str = Field(alias="_id")
    document_id: str
    created_at: datetime

    class Config:
        populate_by_name = True
