import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid6 import uuid7
from core.config import settings


class KYCStatusEnum(str, Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class CreatorStatusEnum(str, Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class RoleEnum(str, Enum):
    GUEST = "guest"
    READER = "reader"
    AUTHOR = "author"
    ADMIN = "admin"


class AITierEnum(str, Enum):
    BASIC = "BASIC"
    PRO = "PRO"
    PREMIUM = "PREMIUM"


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
    creator_status: CreatorStatusEnum = CreatorStatusEnum.NONE
    is_verified: bool = False
    storage_limit: int = Field(
        default=settings.DEFAULT_PAGE_LIMIT * 1024 * 1024 * 1024,
        le=settings.MAX_PAGE_LIMIT * 1024 * 1024 * 1024
    )
    ai_tier: AITierEnum = AITierEnum.BASIC

    @field_validator("kyc_status", "creator_status", mode="before")
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
        "default_visibility": "public",
    }


class UserCreate(UserBase):
    password: str
    agreed_to_terms: bool = False


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


class UserResponse(UserBase):
    id: str = Field(alias="_id")
    created_at: datetime
    has_passkey: bool = False

    class Config:
        populate_by_name = True


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None


class SettingsUpdate(BaseModel):
    theme: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    privacy_mode: Optional[bool] = None


class BrandPageUpdate(BaseModel):
    banner_url: Optional[str] = None
    theme_color: Optional[str] = None
    layout_type: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerifyCodeRequest(BaseModel):
    token: str


class NotificationSettingsUpdate(BaseModel):
    enable_comment_notifications: bool = True
    enable_mention_notifications: bool = True
    enable_system_notifications: bool = True
    enable_email_digest: bool = False


class UpdateRoleRequest(BaseModel):
    role: RoleEnum


class UpdateStatusRequest(BaseModel):
    is_active: bool


class ModerationActionRequest(BaseModel):
    reason: str
    duration_hours: Optional[int] = None


class NoteRequest(BaseModel):
    note: str


class PasskeyRequest(BaseModel):
    email: str


class PasskeyFinishRequest(BaseModel):
    email: str
    credential: dict
