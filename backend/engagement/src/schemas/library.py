from typing import Optional

from pydantic import BaseModel, Field


class ReadingListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    is_public: bool = True
