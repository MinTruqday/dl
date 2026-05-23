from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid
from uuid6 import uuid7

class ReviewBase(BaseModel):
    rating: int
    content: Optional[str] = None
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewInDB(ReviewBase):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    document_id: str
    user_id: str
    full_name: str
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReviewResponse(ReviewInDB):
    id: str = Field(alias="_id")
    class Config:
        populate_by_name = True

class RatingRequest(BaseModel):
    rating: int
    content: Optional[str] = None
    review_text: Optional[str] = None

class ChapterRatingRequest(BaseModel):
    chapter_id: Optional[str] = None
    chapter_slug: Optional[str] = None
    rating: int
