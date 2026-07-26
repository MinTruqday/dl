from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.core.infrastructure.configuration import settings


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CompileRequest(StrictModel):
    content: str = Field(min_length=1, max_length=settings.MAX_COMPILE_INPUT_BYTES)


class KeystrokeSyncRequest(StrictModel):
    content: str = Field(max_length=200000)
    timestamp: Optional[float] = None


class InlineSuggestionRequest(StrictModel):
    selected_text: str = Field(min_length=1, max_length=10000)
    suggested_text: str = Field(min_length=1, max_length=10000)
    comment: Optional[str] = Field(default=None, max_length=5000)


class ResolveSuggestionRequest(StrictModel):
    action: Literal["accepted", "rejected"]


class PomodoroSyncRequest(StrictModel):
    document_id: str = Field(min_length=1, max_length=100)
    duration: int = Field(ge=1, le=1440)
    words_written: int = Field(ge=0, le=1000000)


class FindReplaceRequest(StrictModel):
    search: str = Field(min_length=1, max_length=1000)
    replace: str = Field(max_length=10000)
    match_case: bool = False


class AutoSaveRequest(StrictModel):
    content: dict[str, Any]


class InlineCommentRequest(StrictModel):
    block_id: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=10000)
    selected_text: Optional[str] = Field(default=None, max_length=10000)


class VersionDiffRequest(StrictModel):
    version_id_a: str = Field(min_length=1, max_length=100)
    version_id_b: str = Field(min_length=1, max_length=100)
