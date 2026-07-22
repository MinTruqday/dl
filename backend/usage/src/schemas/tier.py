from pydantic import BaseModel, Field, model_validator
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

    @model_validator(mode="after")
    def validate_premium_state(self):
        expected = self.ai_tier != Tier.BASIC
        if self.is_premium != expected:
            raise ValueError("Trạng thái cao cấp không khớp với gói thành viên")
        return self
