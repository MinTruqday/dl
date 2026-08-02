from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from enum import Enum
from datetime import datetime, timezone
import uuid

class Role(str, Enum):
    GUEST = "guest"
    READER = "reader"
    AUTHOR = "author"
    ADMIN = "admin"

class KYC(str, Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class Creator(str, Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"

class UserBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr
    full_name: str
    slug: str
    role: Role = Role.READER
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    social_links: Optional[Dict[str, str]] = Field(default_factory=dict)
    pinned_documents: List[str] = Field(default_factory=list)
    bookmarks: List[str] = Field(default_factory=list)
    wallet_balance: int = 0
    is_shadowbanned: bool = False
    permissions: List[str] = Field(default_factory=list)
    donation_link: Optional[str] = None
    kyc_status: KYC = KYC.NONE
    creator_status: Creator = Creator.NONE
    is_verified: bool = False
    storage_limit: int = 50 * 1024 * 1024 * 1024
    tos_accepted_at: Optional[datetime] = None
    welcome_message: Optional[str] = None
    blocked_users: List[str] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=lambda: {
        "mod_notifs": True,
        "auto_refresh": False,
        "auto_save": True,
        "default_visibility": "public",
    })

class UserInDB(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    bio: Optional[str] = Field(default=None, max_length=1000)
    avatar_url: Optional[str] = Field(default=None, max_length=2048)
    cover_url: Optional[str] = Field(default=None, max_length=2048)
    location: Optional[str] = Field(default=None, max_length=100)
    website: Optional[str] = Field(default=None, max_length=2048)

class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    role: Role = Role.READER

class UpdateRoleRequest(BaseModel):
    role: Role

class UpdateStatusRequest(BaseModel):
    is_active: bool

class ModerationActionRequest(BaseModel):
    reason: str
    duration_hours: Optional[int] = None

class NoteRequest(BaseModel):
    note: str


class SettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme: Optional[str] = Field(default=None, max_length=30)
    notifications_enabled: Optional[bool] = None
    privacy_mode: Optional[bool] = None
    mod_notifs: Optional[bool] = None
    auto_refresh: Optional[bool] = None
    auto_save: Optional[bool] = None
    default_visibility: Optional[str] = Field(default=None, pattern=r"^(public|private|unlisted)$")


class AuthorApplication(BaseModel):
    motivation: str = Field(min_length=20, max_length=2000)
    portfolio: Optional[str] = Field(default=None, max_length=2048)
