from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

class CollectionRequest(BaseModel):
    source: str
    url: Optional[str] = None
    index_type: Optional[str] = "list"
    target_class: Optional[str] = None
