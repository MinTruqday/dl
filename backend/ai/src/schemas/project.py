from typing import Any

from pydantic import BaseModel, Field, field_validator

KNOWLEDGE_AUTHORITIES = {
    "APPROVED_SOURCE",
    "CONTROLLED_SOURCE",
    "PROJECT_REFERENCE",
    "SUPPLEMENTAL",
    "DRAFT",
    "UNVERIFIED",
}


class ProjectArtifactIndexRequest(BaseModel):
    artifact_type: str = Field(min_length=1, max_length=100)
    artifact_id: str = Field(min_length=1, max_length=200)
    artifact_version_id: str = Field(min_length=1, max_length=200)
    title: str = Field(default="", max_length=500)
    text: str = Field(min_length=1, max_length=50000)
    status: str = Field(default="ACTIVE", max_length=50)
    authority: str = Field(default="PROJECT_REFERENCE", max_length=100)
    version: Any = None
    module: str = Field(default="", max_length=200)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("authority")
    @classmethod
    def validate_authority(cls, value: str) -> str:
        if value not in KNOWLEDGE_AUTHORITIES:
            raise ValueError("AUTHORITY_INVALID")
        return value


class ProjectKnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=10000)
    artifact_types: list[str] = Field(default_factory=list, max_length=20)
    limit: int = Field(default=20, ge=1, le=100)
