from typing import List, Optional
from pydantic import BaseModel, Field

class DocumentSearchResult(BaseModel):
    id: str = Field(alias="_id")
    title: str
    slug: str
    cover_url: Optional[str] = None
    publisher_name: Optional[str] = None
    views: int = 0
    tags: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    semantic_score: Optional[float] = None

    class Config:
        populate_by_name = True
