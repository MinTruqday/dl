from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid

class HighlightCreateRequest(BaseModel):
    text: str
    chapter_slug: str = ""
    color: str = "#e4e4e7"
    start_offset: int = 0
    end_offset: int = 0
    note: str = ""

class HighlightNoteUpdateRequest(BaseModel):
    note: str

class ReadingPreferenceUpdate(BaseModel):
    theme: str = "light"
    font_size: int = 16
    line_height: float = 1.8
    font_family: str = "Inter"
    is_dyslexic_mode: bool = False
