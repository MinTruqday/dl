from typing import Optional
from pydantic import BaseModel

class CollectorRequest(BaseModel):
    source: str
    pages: Optional[int] = 1