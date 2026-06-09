from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

class CollectionRequest(BaseModel):
    source: str
    pages: Optional[int] = 0
