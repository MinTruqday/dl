from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

class ArchiveBase(BaseModel):
    filename: str
    type: str = "image"
    size_bytes: int = 0
    url: str = ""
    is_pinned: bool = False
    is_deleted: bool = False
    description: Optional[str] = ""
    is_public: bool = True
    shared_with: list[str] = []
    email: Optional[str] = ""
    tags: list[str] = []

class ArchiveUploadRequest(ArchiveBase):
    pass

class ArchiveRenameRequest(BaseModel):
    filename: str

class ArchiveDescriptionRequest(BaseModel):
    description: str

class ArchiveShareRequest(BaseModel):
    email: str

class ArchiveTagsRequest(BaseModel):
    tags: list[str]

class ArchiveInDB(ArchiveBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
