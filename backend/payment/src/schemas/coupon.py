from pydantic import BaseModel
from datetime import datetime

class CouponCreateRequest(BaseModel):
    code: str
    discount_percent: float
    max_uses: int
    expires_at: datetime
    amount_dl: int = 0
