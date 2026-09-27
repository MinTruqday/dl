from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.schemas.identity import SystemRole


class CurrentUser(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(alias="_id")
    email: str
    system_role: SystemRole = SystemRole.USER
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = True
    full_name: str = ""
    slug: str = ""
    session_id: str = ""

    @field_validator("system_role", mode="before")
    @classmethod
    def validate_system_role_case(cls, value: Any):
        return value.upper() if isinstance(value, str) else value


T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    data: Optional[T] = None
    message: str
    status: int = 200
