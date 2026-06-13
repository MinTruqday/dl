from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
import math

from pydantic import BaseModel, Field


class QuotaLimit(BaseModel):
    daily_requests: Union[int, float] = 0
    daily_tokens: Union[int, float] = 0
    monthly_requests: Optional[Union[int, float]] = None
    monthly_tokens: Optional[Union[int, float]] = None


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
        "admin": QuotaLimit(daily_requests=math.inf, daily_tokens=math.inf),
    }
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
