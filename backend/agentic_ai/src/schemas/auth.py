from enum import Enum
from typing import List, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Role(str, Enum):
    GUEST = "guest"
    READER = "reader"
    AUTHOR = "author"
    ADMIN = "admin"

class Tier(str, Enum):
    BASIC = "BASIC"
    PRO = "PRO"
    PREMIUM = "PREMIUM"

class CurrentUser(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(alias="_id", description="<input_context>Unique identifier for the user.</input_context>")
    email: str = Field(description="<input_context>User's email address.</input_context>")
    role: Role = Field(default=Role.READER, description="<critical_instructions>The role assigned to the user for access control.</critical_instructions>")
    permissions: List[str] = Field(default_factory=list, description="<critical_instructions>List of specific permissions granted.</critical_instructions>")
    is_active: bool = Field(default=True, description="<conditional_output>Whether the user account is active.</conditional_output>")
    full_name: str = Field(default="", description="<input_context>User's full name.</input_context>")
    slug: str = Field(default="", description="<input_context>URL-friendly username or slug.</input_context>")
    is_premium: bool = Field(default=False, description="<conditional_output>Whether the user has premium access.</conditional_output>")
    ai_tier: Tier = Field(default=Tier.BASIC, description="<conditional_output>The active AI service tier.</conditional_output>")
    
    @field_validator("role", mode="before")
    @classmethod
    def validate_role_case(cls, v: Any):
        if isinstance(v, str):
            return v.lower()
        return v
