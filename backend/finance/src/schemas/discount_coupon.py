from pydantic import BaseModel

class CouponCreateRequest(BaseModel):
    code: str
    discount_percent: float
    max_uses: int
    expires_at: str
