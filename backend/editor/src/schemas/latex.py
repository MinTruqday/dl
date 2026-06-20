from typing import Optional

from pydantic import BaseModel, Field


class CompileRequest(BaseModel):
    content: str = Field(..., max_length=100000)
    is_fragment: bool = False


class FormatRequest(BaseModel):
    content: str = Field(..., max_length=100000)


class ExportRequest(BaseModel):
    content: str = Field(..., max_length=100000)
    format: str = "docx"


class AutoSaveRequest(BaseModel):
    document_id: str
    content: str
