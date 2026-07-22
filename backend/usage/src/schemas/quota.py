from datetime import datetime, timezone
from typing import Dict

from pydantic import BaseModel, Field

class QuotaLimit(BaseModel):
    daily_requests: int = Field(default=0, ge=-1, le=1_000_000)
    daily_tokens: int = Field(default=0, ge=-1, le=1_000_000_000)
    req_reset_hours: int = Field(default=24, ge=1, le=720)
    max_docs: int = Field(default=1, ge=-1, le=1_000_000)
    model: str = Field(default="", max_length=300)
    thinking: bool = False

class UserQuota(BaseModel):
    user_id: str
    role: str
    limits: QuotaLimit
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GlobalQuotaConfig(BaseModel):
    role_limits: Dict[str, QuotaLimit] = Field(default_factory=lambda: {
        "reader": QuotaLimit(daily_requests=0, daily_tokens=0),
        "author": QuotaLimit(daily_requests=0, daily_tokens=0),
        "admin": QuotaLimit(daily_requests=-1, daily_tokens=-1, max_docs=-1),
    })
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConsumeQuotaRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    feature: str = Field(default="chat", pattern=r"^[a-zA-Z0-9_-]{1,50}$")
    req_reset_hours: int = Field(default=24, ge=1, le=720)
    tokens: int = Field(default=0, ge=0, le=10_000_000)

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
    user_id: str = Field(min_length=1, max_length=100)
    item_type: UploadType
    req_reset_hours: int = Field(default=24, ge=1, le=720)
