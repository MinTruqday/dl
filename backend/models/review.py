from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class ReviewBase(BaseModel):
    rating: int
    content: str

class ReviewCreate(ReviewBase):
    pass

class ReviewInDB(ReviewBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    document_id: str
    user_id: str
    full_name: str
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReviewResponse(ReviewInDB):
    id: str = Field(alias="_id")
    class Config:
        populate_by_name = True
