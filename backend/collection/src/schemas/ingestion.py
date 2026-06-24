from typing import Optional

from pydantic import BaseModel

class Collection(BaseModel):
    source: str
    pages: Optional[int] = 1
