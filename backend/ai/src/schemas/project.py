from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.core.policies import document_policy

PROJECT_KNOWLEDGE_POLICY = document_policy()["project_knowledge"]
RETRIEVAL_POLICY = document_policy()["retrieval"]
KNOWLEDGE_AUTHORITIES = frozenset(PROJECT_KNOWLEDGE_POLICY["authorities"])


class ProjectArtifactIndexRequest(BaseModel):
    artifact_type: str = Field(
        min_length=1, max_length=PROJECT_KNOWLEDGE_POLICY["artifact_type_maximum_characters"]
    )
    artifact_id: str = Field(
        min_length=1,
        max_length=PROJECT_KNOWLEDGE_POLICY["artifact_identifier_maximum_characters"],
    )
    artifact_version_id: str = Field(
        min_length=1,
        max_length=PROJECT_KNOWLEDGE_POLICY["artifact_identifier_maximum_characters"],
    )
    title: str = Field(
        default="", max_length=PROJECT_KNOWLEDGE_POLICY["title_maximum_characters"]
    )
    text: str = Field(
        min_length=1, max_length=PROJECT_KNOWLEDGE_POLICY["maximum_artifact_characters"]
    )
    status: str = Field(
        default="ACTIVE", max_length=PROJECT_KNOWLEDGE_POLICY["status_maximum_characters"]
    )
    authority: str = Field(
        default="PROJECT_REFERENCE",
        max_length=PROJECT_KNOWLEDGE_POLICY["authority_maximum_characters"],
    )
    version: Any = None
    module: str = Field(
        default="", max_length=PROJECT_KNOWLEDGE_POLICY["module_maximum_characters"]
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("authority")
    @classmethod
    def validate_authority(cls, value: str) -> str:
        if value not in KNOWLEDGE_AUTHORITIES:
            raise ValueError("AUTHORITY_INVALID")
        return value


class ProjectKnowledgeSearchRequest(BaseModel):
    query: str = Field(
        min_length=1, max_length=RETRIEVAL_POLICY["maximum_query_characters"]
    )
    artifact_types: list[str] = Field(
        default_factory=list,
        max_length=PROJECT_KNOWLEDGE_POLICY["artifact_types_maximum_count"],
    )
    limit: int = Field(
        default=PROJECT_KNOWLEDGE_POLICY["default_search_result_count"],
        ge=1,
        le=PROJECT_KNOWLEDGE_POLICY["maximum_search_result_count"],
    )
