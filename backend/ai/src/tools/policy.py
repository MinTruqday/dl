from typing import Any, Literal

from pydantic import BaseModel

from src.runtime.models import SpecialistName


class ToolVerification(BaseModel):
    path: str
    identifier: str
    expected: dict[str, Any]


class ToolPolicy(BaseModel):
    name: str
    specialists: set[SpecialistName]
    action: Literal["READ", "PROPOSE", "MUTATE"]
    permission: str
    requires_approval: bool
    verification: ToolVerification | None = None


class ToolDecision(BaseModel):
    allowed: bool
    reason_code: str
    policy: ToolPolicy | None = None
