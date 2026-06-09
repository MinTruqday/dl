from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class EditorBlock(BaseModel):
    id: Optional[str] = None
    type: str
    data: Dict[str, Any] = {}

class EditorJSContent(BaseModel):
    time: Optional[int] = None
    blocks: List[EditorBlock] = []
    version: Optional[str] = None

class EditorJSCompileRequest(BaseModel):
    content: EditorJSContent
    title: Optional[str] = Field(None, max_length=500)
    author: Optional[str] = Field(None, max_length=200)
    font_size: Optional[int] = Field(12, ge=8, le=24)
    paper_size: Optional[str] = Field("a4paper", pattern="^(a4paper|letterpaper|a3paper)$")
    export_format: Optional[str] = Field("pdf", pattern="^(pdf|docx|html)$")
