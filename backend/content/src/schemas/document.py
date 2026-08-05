import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

class DocumentStatus(str, Enum):
    DRAFT = "draft"
    COMPILING = "compiling"
    COMPILING_LATEX = "compiling_latex"
    PROCESSING_PUBLISH = "processing_publish"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class DocumentContentFormat(str, Enum):
    DOCLIBX = "doclibx"
    MARKDOWN = "markdown"
    CUSTOM = "custom"
    PDF = "pdf"
    ZIP = "zip"
    HTML = "html"
    DOCLIB = "doclib"

class DocumentBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=300)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: Optional[str] = Field(default=None, max_length=5000)
    cover_url: Optional[str] = None
    file_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list, max_length=50)
    content: Optional[Any] = None
    content_format: Optional[DocumentContentFormat] = DocumentContentFormat.DOCLIB
    price_dl: int = Field(default=0, ge=0, le=1_000_000_000)
    visibility: str = Field(default="public", pattern=r"^(public|private|unlisted)$")
    category: Optional[str] = "Uncategorized"
    pages_count: Optional[int] = 0
    preview_pages: int = Field(default=5, ge=0, le=1000)
    scheduled_publish_at: Optional[datetime] = None
    coauthors: List[str] = Field(default_factory=list)
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    publisher_name: Optional[str] = None
    folder_id: Optional[str] = None
    drm_settings: Optional[dict] = None
    publish_at: Optional[datetime] = None
    draft_content: Optional[Any] = None
    toc: List[dict] = Field(default_factory=list)
    reading_time_minutes: int = 0

class DocumentContentUpdate(BaseModel):
    content: Any
    content_format: str
    expected_version: Optional[datetime] = None

class DocumentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    price_dl: Optional[int] = Field(default=None, ge=0, le=1_000_000_000)
    folder_id: Optional[str] = None
    drm_settings: Optional[dict] = None
    publish_at: Optional[datetime] = None
    scheduled_publish_at: Optional[datetime] = None
    expected_version: Optional[datetime] = None

class DocumentCreate(DocumentBase):
    password: Optional[str] = Field(default=None, min_length=8, max_length=200)

class DocumentInDB(DocumentBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    creator_id: str
    status: DocumentStatus = DocumentStatus.DRAFT
    drm_fingerprint: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    views: int = 0

class DocumentResponse(DocumentBase):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(alias="_id")
    creator_id: str
    status: DocumentStatus
    created_at: datetime
    views: int = 0
    has_purchased: bool = False

class DocumentPasswordRequest(BaseModel):
    password: str = Field(min_length=8, max_length=200)

class SchedulePublishRequest(BaseModel):
    publish_at: datetime

class SeoMetadataRequest(BaseModel):
    tags: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    slug: str = ""
    description: str = ""

class CoauthorInviteRequest(BaseModel):
    document_id: Optional[str] = None
    email: str
    role: str = "editor"

class CollaborationResponse(BaseModel):
    status: str


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

class TagsUpdate(BaseModel):
    tags: List[str]

class ScheduleUpdate(BaseModel):
    publish_at: datetime


class CollaborationShareLinkConfig(BaseModel):
    is_active: bool = True
    password: Optional[str] = None
    default_role: str = "editor"
    expires_in_hours: Optional[int] = None


class CollaborationShareLinkJoin(BaseModel):
    password: Optional[str] = None


class CollaborationAccessRequestCreate(BaseModel):
    requested_role: str = "editor"
    message: Optional[str] = None


class CollaborationAccessRequestReview(BaseModel):
    status: str
    role: Optional[str] = None

