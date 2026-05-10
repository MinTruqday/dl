from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class QuotaLimit(BaseModel):
    daily_requests: int = 10
    daily_tokens: int = 5000
    monthly_requests: Optional[int] = None
    monthly_tokens: Optional[int] = None

class UserQuota(BaseModel):
    user_id: str
    role: str
    limits: QuotaLimit
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GlobalQuotaConfig(BaseModel):
    role_limits: Dict[str, QuotaLimit] = {
        "reader": QuotaLimit(daily_requests=20, daily_tokens=10000),
        "author": QuotaLimit(daily_requests=100, daily_tokens=50000),
        "moderator": QuotaLimit(daily_requests=500, daily_tokens=200000),
        "admin": QuotaLimit(daily_requests=999999, daily_tokens=999999)
    }
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
