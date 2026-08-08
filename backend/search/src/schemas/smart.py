from typing import List, Optional
from pydantic import BaseModel, Field

class SmartSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=20, ge=1, le=100)
