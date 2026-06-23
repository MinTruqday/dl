from typing import Optional

from pydantic import BaseModel, Field
from typing import Any

class CompileRequest(BaseModel):
    content: Any


class KeystrokeSyncRequest(BaseModel):
    content: str
    timestamp: Optional[float] = None


class InlineSuggestionRequest(BaseModel):
    selected_text: str
    suggested_text: str
    comment: Optional[str] = None


class ResolveSuggestionRequest(BaseModel):
    action: str = Field(..., description="Chọn 'chấp nhận' hoặc 'từ chối'")


class PomodoroSyncRequest(BaseModel):
    document_id: str
    duration: int
    words_written: int


class FindReplaceRequest(BaseModel):
    search: str
    replace: str
    match_case: bool = False


class AutoSaveRequest(BaseModel):
    content: dict


class InlineCommentRequest(BaseModel):
    block_id: str
    text: str
    selected_text: Optional[str] = None


class VersionDiffRequest(BaseModel):
    version_id_a: str
    version_id_b: str
