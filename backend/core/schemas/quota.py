from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class QuotaLimit(BaseModel):
    daily_requests: int = 0
    daily_tokens: int = 0
    monthly_requests: Optional[int] = None
    monthly_tokens: Optional[int] = None

class UserQuota(BaseModel):
    user_id: str
    role: str
    limits: QuotaLimit
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GlobalQuotaConfig(BaseModel):
    role_limits: Dict[str, QuotaLimit] = {
        "reader": QuotaLimit(daily_requests=0, daily_tokens=0),
        "author": QuotaLimit(daily_requests=0, daily_tokens=0),
        "moderator": QuotaLimit(daily_requests=0, daily_tokens=0),
        "admin": QuotaLimit(daily_requests=float('inf'), daily_tokens=float('inf'))
    }
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
