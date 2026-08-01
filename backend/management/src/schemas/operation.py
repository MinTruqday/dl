from typing import Any

from pydantic import BaseModel, Field


class SystemConfigUpdate(BaseModel):
    registration_enabled: bool | None = None


class ShadowbanUpdate(BaseModel):
    status: bool


class KYCUpdate(BaseModel):
    status: str = Field(pattern=r"^(PENDING|VERIFIED|REJECTED)$")


class ReportStatusUpdate(BaseModel):
    status: str = Field(pattern=r"^(RESOLVED|DISMISSED)$")
