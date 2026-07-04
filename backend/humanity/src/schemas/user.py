from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from datetime import datetime, timezone
from uuid6 import uuid7

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

class Tier(str, Enum):
    BASIC = "BASIC"
    PRO = "PRO"
    PREMIUM = "PREMIUM"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    slug: str
    role: Role = Role.READER
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    social_links: Optional[Dict[str, str]] = {}
    pinned_documents: List[str] = []
    bookmarks: List[str] = []
    is_premium: bool = False
    wallet_balance: int = 0
    is_shadowbanned: bool = False
    permissions: List[str] = []
    donation_link: Optional[str] = None
    kyc_status: KYC = KYC.NONE
    creator_status: Creator = Creator.NONE
    is_verified: bool = False
    storage_limit: int = 50 * 1024 * 1024 * 1024
    ai_tier: Tier = Tier.BASIC
    tos_accepted_at: Optional[datetime] = None
    welcome_message: Optional[str] = None
    blocked_users: List[str] = []
    settings: Dict[str, Any] = {
        "mod_notifs": True,
        "auto_refresh": False,
        "auto_save": True,
        "default_visibility": "public",
    }

class UserInDB(UserBase):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None

class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str
    slug: str
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
