import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field
from uuid6 import uuid7


class DocumentStatus(str, Enum):
    DRAFT = "draft"
    COMPILING = "compiling"
    COMPILING_LATEX = "compiling_latex"
    PROCESSING_PUBLISH = "processing_publish"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DocumentContentFormat(str, Enum):
    LATEX = "latex"
    MARKDOWN = "markdown"
    CUSTOM = "custom"
    COMIC = "comic"
    PDF = "pdf"
    EPUB = "epub"
    MOBI = "mobi"
    ZIP = "zip"
    HTML = "html"
    JSON = "json"


class DocumentBase(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    file_url: Optional[str] = None
    tags: List[str] = []
    content: Optional[Any] = None
    content_format: Optional[DocumentContentFormat] = DocumentContentFormat.JSON
    price_dl: int = 0
    visibility: str = "public"
    password: Optional[str] = None
    category: Optional[str] = "Uncategorized"
    pages_count: Optional[int] = 0
    preview_pages: int = 5
    scheduled_publish_at: Optional[datetime] = None
    coauthors: List[str] = []
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    flash_sale: Optional[dict] = None
    publisher_name: Optional[str] = None
    folder_id: Optional[str] = None
    drm_settings: Optional[dict] = None
    publish_at: Optional[datetime] = None
    is_nsfw: Optional[bool] = None
    draft_content: Optional[Any] = None
    toc: List[dict] = []
    reading_time_minutes: int = 0


class DocumentContentUpdate(BaseModel):
    content: Any
    content_format: str
    expected_version: Optional[datetime] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    price_dl: Optional[int] = None
    folder_id: Optional[str] = None
    drm_settings: Optional[dict] = None
    publish_at: Optional[datetime] = None
    scheduled_publish_at: Optional[datetime] = None
    is_nsfw: Optional[bool] = None
    expected_version: Optional[datetime] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentInDB(DocumentBase):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    creator_id: str
    status: DocumentStatus = DocumentStatus.DRAFT
    drm_fingerprint: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    views: int = 0
    average_rating: float = 0.0
    rating_count: int = 0


class DocumentResponse(DocumentBase):
    id: str = Field(alias="_id")
    creator_id: str
    status: DocumentStatus
    created_at: datetime
    views: int = 0
    average_rating: float = 0.0
    rating_count: int = 0
    has_purchased: bool = False

    class Config:
        populate_by_name = True


class DocumentPasswordRequest(BaseModel):
    password: str


class SchedulePublishRequest(BaseModel):
    publish_at: str


class SeoMetadataRequest(BaseModel):
    tags: List[str] = []
    keywords: List[str] = []
    slug: str = ""
    description: str = ""


class CoauthorInviteRequest(BaseModel):
    document_id: Optional[str] = None
    email: str
    role: str = "editor"


class CollaborationResponse(BaseModel):
    status: str


class ModerateDocumentRequest(BaseModel):
    action: str
    reason: str


class TransferOwnershipRequest(BaseModel):
    user_id: str


class UpdateCollaboratorRoleRequest(BaseModel):
    role: str


class CollabMemoCreateRequest(BaseModel):
    message: str


class UpdateCollabAccessRequest(BaseModel):
    access_level: str


class CreateDraftSnapshotRequest(BaseModel):
    version_name: str


class CollabTaskCreateRequest(BaseModel):
    task_desc: str
    assigned_to: Optional[str] = None


class UpdateTaskStatusRequest(BaseModel):
    is_done: bool


class TaskCommentCreateRequest(BaseModel):
    comment_text: str


class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None


class DRMSettingsUpdate(BaseModel):
    disable_copy: bool = False
    hide_from_search: bool = False


class TagsUpdate(BaseModel):
    tags: List[str]


class ScheduleUpdate(BaseModel):
    publish_at: str
