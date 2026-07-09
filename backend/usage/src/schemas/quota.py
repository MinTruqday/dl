import math
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field

class QuotaLimit(BaseModel):
    daily_requests: Union[int, float] = 0
    daily_tokens: Union[int, float] = 0
    req_reset_hours: Union[int, float] = 24
    max_docs: Union[int, float] = 1
    model: str = ""
    thinking: bool = False

class UserQuota(BaseModel):
    user_id: str
    role: str
    limits: QuotaLimit
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GlobalQuotaConfig(BaseModel):
    role_limits: Dict[str, QuotaLimit] = {
        "reader": QuotaLimit(daily_requests=0, daily_tokens=0),
        "author": QuotaLimit(daily_requests=0, daily_tokens=0),
        "admin": QuotaLimit(daily_requests=math.inf, daily_tokens=math.inf),
    }
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConsumeQuotaRequest(BaseModel):
    user_id: str
    feature: str = "chat"
    req_reset_hours: int = 24
    tokens: int = 0

from enum import Enum
class Tier(str, Enum):
    BASIC = "BASIC"
    PRO = "PRO"
    PREMIUM = "PREMIUM"

class UploadType(str, Enum):
    IMAGE = "image"
    DOCUMENT = "document"
    FOLDER = "folder"

class ConsumeUploadQuotaRequest(BaseModel):
    user_id: str
    item_type: UploadType
    req_reset_hours: int = 24
