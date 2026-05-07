from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import uuid

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
