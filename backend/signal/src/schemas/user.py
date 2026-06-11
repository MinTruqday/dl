from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid6 import uuid7
from enum import Enum

class KYCStatusEnum(str, Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class AuthorStatusEnum(str, Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"

class RoleEnum(str, Enum):
    GUEST = "guest"
    READER = "reader"
    POTENTIAL_AUTHOR = "potential_author"
    AUTHOR = "author"
    MODERATOR = "moderator"
    ADMIN = "admin"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    slug: str
    role: RoleEnum = RoleEnum.READER
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    social_links: Optional[Dict[str, str]] = {}
    pinned_documents: List[str] = []
    bookmarks: List[str] = []
    badges: List[str] = []
    is_premium: bool = False
    wallet_balance: int = 0
    is_shadowbanned: bool = False
    permissions: List[str] = []
    donation_link: Optional[str] = None
    kyc_status: KYCStatusEnum = KYCStatusEnum.NONE
    author_status: AuthorStatusEnum = AuthorStatusEnum.NONE
    is_verified: bool = False
    storage_limit: int = 1 * 1024 * 1024 * 1024

    @field_validator("kyc_status", "author_status", mode="before")
    @classmethod
    def validate_enum_case(cls, v: Any):
        if isinstance(v, str):
            return v.upper()
        return v
    tos_accepted_at: Optional[datetime] = None
    welcome_message: Optional[str] = None
    blocked_users: List[str] = []
    settings: Dict[str, Any] = {
        "mod_notifs": True,
        "auto_refresh": False,
        "auto_save": True,
        "default_visibility": "public"
    }

class UserInDB(UserBase):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    read_streak: int = 0
    last_read_date: Optional[datetime] = None
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    is_kyc_verified: bool = False
    passkeys: List[Dict[str, Any]] = []
    last_password_change: Optional[datetime] = None
    last_bank_update: Optional[datetime] = None
