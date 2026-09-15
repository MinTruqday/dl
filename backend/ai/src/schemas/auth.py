from enum import Enum
from typing import Any, List

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Role(str, Enum):
    GUEST = "guest"
    READER = "reader"
    AUTHOR = "author"
    ADMIN = "admin"


class SystemRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class CurrentUser(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(alias="_id")
    email: str
    role: Role = Role.READER
    system_role: SystemRole = SystemRole.USER
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = True
    full_name: str = ""
    slug: str = ""
    session_id: str = ""

    @field_validator("role", mode="before")
    @classmethod
    def validate_role_case(cls, v: Any):
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("system_role", mode="before")
    @classmethod
    def validate_system_role_case(cls, v: Any):
        if isinstance(v, str):
            return v.upper()
        return v
