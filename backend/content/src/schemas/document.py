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
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    TXT = "txt"
    LATEX = "latex"
    EPUB = "epub"
    CSV = "csv"


class ArtifactMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=128)
    artifact_type: str = Field(default="project_document", min_length=1, max_length=100)
    artifact_id: Optional[str] = Field(default=None, max_length=128)
    artifact_version_id: Optional[str] = Field(default=None, max_length=128)
    module: Optional[str] = Field(default=None, max_length=200)
    status: str = Field(default="active", min_length=1, max_length=100)
    authority: str = Field(default="reference", min_length=1, max_length=100)
    source_type: str = Field(default="project_document", min_length=1, max_length=100)
    source_version: Optional[str] = Field(default=None, max_length=200)
    content_type: Optional[str] = Field(default=None, max_length=100)
    conflict_key: Optional[str] = Field(default=None, max_length=200)
    claim_value: Optional[str] = Field(default=None, max_length=500)


class DocumentBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=300)
    slug: Optional[str] = Field(
        default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    description: Optional[str] = Field(default=None, max_length=5000)
    cover_url: Optional[str] = None
    file_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list, max_length=50)
    content: Optional[Any] = None
    content_format: Optional[DocumentContentFormat] = DocumentContentFormat.DOCLIB
    visibility: str = Field(default="public", pattern=r"^(public|private|unlisted)$")
    category: Optional[str] = "Uncategorized"
    pages_count: Optional[int] = 0
    preview_pages: int = Field(default=5, ge=0, le=1000)
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    publisher_name: Optional[str] = None
    folder_id: Optional[str] = None
    draft_content: Optional[Any] = None
    toc: List[dict] = Field(default_factory=list)
    reading_time_minutes: int = 0
    artifact_metadata: Optional[ArtifactMetadata] = None


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
    folder_id: Optional[str] = None
    expected_version: Optional[datetime] = None
    file_url: Optional[str] = None
    content_format: Optional[DocumentContentFormat] = None
    artifact_metadata: Optional[ArtifactMetadata] = None


class DocumentCreate(DocumentBase):
    password: Optional[str] = Field(default=None, min_length=8, max_length=200)


class DocumentInDB(DocumentBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    creator_id: str
    status: DocumentStatus = DocumentStatus.DRAFT
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


class DocumentPasswordRequest(BaseModel):
    password: str = Field(min_length=8, max_length=200)


class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None


class TagsUpdate(BaseModel):
    tags: List[str]
