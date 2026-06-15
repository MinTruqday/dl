from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid6 import uuid7

class ShareAccess(BaseModel):
    user_id: str
    role: str = "viewer"

class StorageItemBase(BaseModel):
    name: str
    parent_id: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    tags: List[str] = []
    shared_with: List[ShareAccess] = []
    is_shortcut: bool = False
    target_id: Optional[str] = None
    is_duplicate: Optional[bool] = False
    duplicate_of: Optional[str] = None
    environment_ready: Optional[bool] = False
    ai_processed: Optional[bool] = False
    entities: Optional[dict] = {}
    broken_links: Optional[List[str]] = []

class StorageItemCreate(StorageItemBase):
    is_folder: bool = False
    size: int = 0
    mime_type: Optional[str] = None
    url: Optional[str] = None

class StorageItemUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    tags: Optional[List[str]] = None
    is_trashed: Optional[bool] = None
    is_starred: Optional[bool] = None
    is_public: Optional[bool] = None
    shared_with: Optional[List[ShareAccess]] = None
    is_duplicate: Optional[bool] = None
    duplicate_of: Optional[str] = None
    environment_ready: Optional[bool] = None
    ai_processed: Optional[bool] = None
    entities: Optional[dict] = None
    broken_links: Optional[List[str]] = None

class FileVersion(BaseModel):
    version_id: str = Field(default_factory=lambda: str(uuid7()))
    url: str
    size: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StorageItemInDB(StorageItemBase):
    id: str = Field(default_factory=lambda: str(uuid7()))
    owner_id: str
    is_folder: bool = False
    size: int = 0
    mime_type: Optional[str] = None
    url: Optional[str] = None
    is_trashed: bool = False
    is_starred: bool = False
    is_public: bool = False
    share_token: Optional[str] = None
    versions: List[FileVersion] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StorageItemResponse(StorageItemBase):
    id: str = Field()
    owner_id: str
    is_folder: bool
    size: int
    mime_type: Optional[str]
    url: Optional[str]
    color: Optional[str] = None
    is_trashed: bool
    is_starred: bool
    is_public: bool = False
    share_token: Optional[str] = None
    versions: List[FileVersion] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True