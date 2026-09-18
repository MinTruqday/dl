from typing import Any, Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """
    Trigger asynchronous ingestion of a document into the knowledge vector store.
    Constraint: Requires document_id mapping to the external document storage DB.
    """

    document_id: str = Field(
        description="<critical_instructions>The ID of the document to ingest.</critical_instructions>"
    )
    requester_id: Optional[str] = None
    is_admin: bool = False


class IngestResponse(BaseModel):
    document_id: str
    status: str
    chunks_count: int
    summary_generated: bool = False
    extraction_method: str = "local"
    quarantined_chunks: list[dict[str, Any]] = Field(default_factory=list)
    failed_chunks: list[dict[str, Any]] = Field(default_factory=list)


class AttachmentConversionRequest(BaseModel):
    data: str = Field(min_length=1, max_length=35_000_000)
    filename: str = Field(default="attachment.pdf", min_length=1, max_length=255)
