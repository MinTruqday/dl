from typing import Optional
from pydantic import BaseModel

class CampaignRequest(BaseModel):
    title: str
    target: str = "ALL"
    discount: int = 0
