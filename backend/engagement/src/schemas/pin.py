from typing import List
from pydantic import BaseModel, Field, ConfigDict

class PinnedDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    document_ids: List[str] = Field(description="<critical_instructions>List of document identifiers to pin</critical_instructions>")
