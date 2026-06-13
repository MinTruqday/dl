import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel


class HighlightCreateRequest(BaseModel):
    text: str
    color: str = "#e4e4e7"
    start_offset: int = 0
    end_offset: int = 0
    note: str = ""


class HighlightNoteUpdateRequest(BaseModel):
    note: str


class ReadingPreferenceUpdate(BaseModel):
    theme: Optional[str] = None
    font_size: Optional[int] = None
    line_height: Optional[float] = None
    font_family: Optional[str] = None
    letter_spacing: Optional[float] = None
    is_dyslexic_mode: Optional[bool] = None
