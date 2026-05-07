from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from enum import Enum

class Chapter(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    order: int
    is_premium: bool = False
    price_dl: int = Field(default=0, alias="price_dl")
    words_count: int = 0
    locked: bool = False
    readability_score: float = 0.0
    vocabulary_richness: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True

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

class DocumentBase(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    file_url: Optional[str] = None
    tags: List[str] = []
    content: Optional[str] = None
    content_format: Optional[DocumentContentFormat] = DocumentContentFormat.LATEX
    price_dl: int = 0
    visibility: str = "public"
    password: Optional[str] = None
    category: Optional[str] = "Chưa phân loại"
    pages_count: Optional[int] = 0
    preview_pages: int = 5
    scheduled_publish_at: Optional[datetime] = None
    chapters: List[Chapter] = []
    coauthors: List[str] = []
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    flash_sale: Optional[dict] = None
    publisher_name: Optional[str] = None


class DocumentContentUpdate(BaseModel):
    content: str
    content_format: str

class DocumentCreate(DocumentBase):
    pass

class DocumentInDB(DocumentBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    author_id: str
    status: DocumentStatus = DocumentStatus.DRAFT
    drm_fingerprint: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    views: int = 0
    average_rating: float = 0.0
    rating_count: int = 0

class DocumentResponse(DocumentBase):
    id: str = Field(alias="_id")
    author_id: str
    status: DocumentStatus
    created_at: datetime
    views: int = 0
    average_rating: float = 0.0
    rating_count: int = 0
    has_purchased: bool = False
    
    class Config:
        populate_by_name = True
