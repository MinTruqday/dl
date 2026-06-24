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

class ProgressUpdate(BaseModel):
    document_id: str
    progress_percentage: float

class PinnedDocumentRequest(BaseModel):
    document_ids: List[str]
