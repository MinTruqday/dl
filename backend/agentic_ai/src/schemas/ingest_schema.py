from pydantic import BaseModel


class IngestRequest(BaseModel):
    document_id: str
