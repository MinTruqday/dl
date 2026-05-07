from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

class CompileRequest(BaseModel):
    content: str
    is_fragment: bool = False

class FormatRequest(BaseModel):
    content: str

class ExportRequest(BaseModel):
    content: str
    format: str = "docx"

class AutoSaveRequest(BaseModel):
    document_id: str
    content: str
