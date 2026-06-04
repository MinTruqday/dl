from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import json

class DocumentContentFormat(str, Enum):
    LATEX = "latex"
    JSON = "json"

class DocumentBase(BaseModel):
    content_format: Optional[DocumentContentFormat] = DocumentContentFormat.JSON

class DocumentResponse(DocumentBase):
    id: str = Field(alias="_id")

resp = DocumentResponse(**{"_id": "123", "content_format": "latex"})
print(resp.model_dump_json())
