from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class Tier(str, Enum):
    BASIC = "BASIC"
    PRO = "PRO"
    PREMIUM = "PREMIUM"

class UsageTierResponse(BaseModel):
    user_id: str
    ai_tier: Tier
    is_premium: bool

class UpdateTierRequest(BaseModel):
    ai_tier: Tier
    is_premium: bool
