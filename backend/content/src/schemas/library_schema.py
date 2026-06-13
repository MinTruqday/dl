import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class ReadingListBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = True


class ReadingListCreate(ReadingListBase):
    pass


class BookmarkFolderBase(BaseModel):
    name: str
    color: Optional[str] = "#3b82f6"


class BookmarkFolderCreate(BookmarkFolderBase):
    pass


class BookmarkFolderAssign(BaseModel):
    folder_id: str
    document_ids: List[str]


class TypographyRequest(BaseModel):
    font_family: Optional[str] = "Inter"
    font_size: Optional[int] = 16
    line_height: Optional[float] = 1.8
    letter_spacing: Optional[float] = 0.0


class ProgressUpdate(BaseModel):
    document_id: str
    progress_percentage: float


class ReadingGoalCreate(BaseModel):
    target_documents: int
    target_pages: int
    period: str = "monthly"


class PinnedDocumentRequest(BaseModel):
    document_ids: List[str]
