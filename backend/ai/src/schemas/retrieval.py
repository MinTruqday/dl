from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.core.policies import document_policy


RETRIEVAL_POLICY = document_policy()["retrieval"]


class ArtifactFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: Optional[str] = None
    artifact_type: Optional[str] = None
    artifact_id: Optional[str] = None
    artifact_version_id: Optional[str] = None
    module: Optional[str] = None
    status: Optional[str] = None
    authority: Optional[List[str]] = None
    source_type: Optional[str] = None
    source_version: Optional[str] = None
    content_type: Optional[str] = None


class RetrieveRequest(BaseModel):
    query: str = Field(
        min_length=1, max_length=RETRIEVAL_POLICY["maximum_query_characters"]
    )
    document_ids: Optional[List[str]] = None
    k: int = Field(
        default=RETRIEVAL_POLICY["default_result_count"],
        ge=1,
        le=RETRIEVAL_POLICY["maximum_candidate_count"],
    )
    query_vector_override: Optional[List[float]] = None
    requester_id: Optional[str] = None
    is_admin: bool = False
    metadata_filters: ArtifactFilters = Field(default_factory=ArtifactFilters)


class MultiQueryRetrieveRequest(BaseModel):
    question: str = Field(
        min_length=1, max_length=RETRIEVAL_POLICY["maximum_query_characters"]
    )
    document_ids: Optional[List[str]] = None
    k: int = Field(
        default=RETRIEVAL_POLICY["default_result_count"],
        ge=1,
        le=RETRIEVAL_POLICY["maximum_candidate_count"],
    )
    requester_id: Optional[str] = None
    is_admin: bool = False
    metadata_filters: ArtifactFilters = Field(default_factory=ArtifactFilters)


class CrossDocRetrieveRequest(BaseModel):
    question: str = Field(
        min_length=1, max_length=RETRIEVAL_POLICY["maximum_query_characters"]
    )
    document_ids: List[str]
    k: int = Field(
        default=RETRIEVAL_POLICY["default_result_count"],
        ge=1,
        le=RETRIEVAL_POLICY["maximum_candidate_count"],
    )
    requester_id: Optional[str] = None
    is_admin: bool = False
    metadata_filters: ArtifactFilters = Field(default_factory=ArtifactFilters)


class RetrievedDocument(BaseModel):
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0


class CitationItem(BaseModel):
    chunk_id: str = ""
    document_id: str = ""
    title: str = ""
    chunk_index: Any = ""
    label: str = ""


class RetrieveResponse(BaseModel):
    documents: List[RetrievedDocument]
    citations: List[CitationItem] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
