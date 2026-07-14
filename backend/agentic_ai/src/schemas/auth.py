from enum import Enum
from typing import List, Any
from pydantic import BaseModel, Field, field_validator

class Role(str, Enum):
    GUEST = "guest"
    READER = "reader"
    AUTHOR = "author"
    ADMIN = "admin"

class CurrentUser(BaseModel):
    id: str = Field(alias="_id")
    email: str
    role: Role = Role.READER
    permissions: List[str] = []
    is_active: bool = True
    full_name: str = ""
    slug: str = ""
    is_premium: bool = False
    
    @field_validator("role", mode="before")
    @classmethod
    def validate_role_case(cls, v: Any):
        if isinstance(v, str):
            return v.lower()
        return v
    
    class Config:
        populate_by_name = True
        extra = "ignore"
