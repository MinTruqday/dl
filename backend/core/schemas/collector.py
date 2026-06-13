from pydantic import BaseModel
from typing import Optional

class CollectionRequest(BaseModel):
    source: str
    pages: Optional[int] = 1
