from typing import Literal

from pydantic import BaseModel

class PurchaseRequest(BaseModel):
    document_id: str

class MembershipRequest(BaseModel):
    tier: Literal["PRO", "PREMIUM"]
