from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """
    Trigger asynchronous ingestion of a document into the RAG vector store.
    Constraint: Requires document_id mapping to the external document storage DB.
    """

    document_id: str = Field(
        description="<critical_instructions>The ID of the document to ingest.</critical_instructions>"
    )
