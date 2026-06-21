from typing import Optional
from pydantic import BaseModel

class CollectionRequest(BaseModel):
    source: str
    pages: Optional[int] = 1

class CampaignRequest(BaseModel):
    title: str
    target: str = "ALL"
    discount: int = 0
