from pydantic import BaseModel
from typing import Optional

class CampaignRequest(BaseModel):
    title: str
    target: str = "ALL"
    discount: int = 0

class CollectionRequest(BaseModel):
    source: str
    pages: Optional[int] = 1
