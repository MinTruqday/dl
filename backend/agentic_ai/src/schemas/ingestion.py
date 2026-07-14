from pydantic import BaseModel

class IngestRequest(BaseModel):
    """
    <schema_definition>
    <purpose>Trigger asynchronous ingestion of a document into the RAG vector store.</purpose>
    <metis_constraint>The document_id MUST be a valid, existing document in the primary database.</metis_constraint>
    </schema_definition>
    """
    document_id: str
