from pydantic import BaseModel

class PurchaseRequest(BaseModel):
    document_id: str
    coupon_code: str = None

class MembershipRequest(BaseModel):
    tier: str
