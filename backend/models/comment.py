from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid

class CommentBase(BaseModel):
    item_id: str
    item_type: str
    text: str
    media_url: Optional[str] = None
    parent_id: Optional[str] = None
    path: str = "," 
    is_shadowbanned_content: bool = False

class CommentCreate(CommentBase):
    pass

class CommentInDB(CommentBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    likes_count: int = 0
    liked_by: List[str] = []

class CommentResponse(CommentInDB):
    id: str = Field(alias="_id")
    user: Optional[Dict] = None
    class Config:
        populate_by_name = True
