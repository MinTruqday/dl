from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class EnvironmentIncidentCreate(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)
    environment_id: str = Field(min_length=1, max_length=200)
    build_id: str | None = Field(default=None, max_length=200)
    observed_at: datetime
    severity: Literal["BLOCKER", "CRITICAL", "MAJOR", "MINOR"]
    type: Literal["UNAVAILABLE", "DEPLOYMENT_FAILURE", "TEST_DATA_FAILURE", "NETWORK", "DEPENDENCY", "CONFIGURATION", "CAPACITY", "CERTIFICATE", "OTHER"]
    description: str = Field(min_length=2, max_length=10000)
    affected_run_ids: list[str] = Field(default_factory=list, max_length=1000)
    evidence_refs: list[str] = Field(default_factory=list, max_length=1000)
    owner_id: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_observed_at(self):
        if self.observed_at.tzinfo is None:
            raise ValueError("Thời điểm quan sát phải có múi giờ")
        return self


class EnvironmentIncidentPatch(BaseModel):
    expected_revision: int = Field(ge=1)
    severity: Literal["BLOCKER", "CRITICAL", "MAJOR", "MINOR"] | None = None
    description: str | None = Field(default=None, min_length=2, max_length=10000)
    affected_run_ids: list[str] | None = Field(default=None, max_length=1000)
    evidence_refs: list[str] | None = Field(default=None, max_length=1000)
    owner_id: str | None = Field(default=None, min_length=1, max_length=200)


class EnvironmentIncidentTransition(BaseModel):
    expected_revision: int = Field(ge=1)
    status: Literal["INVESTIGATING", "RESOLVED", "CLOSED"]
    resolution: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def validate_resolution(self):
        if self.status in {"RESOLVED", "CLOSED"} and not self.resolution.strip():
            raise ValueError("Incident đã xử lý phải có kết quả")
        return self
