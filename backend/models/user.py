from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from enum import Enum

class KYCStatusEnum(str, Enum):
    NONE = "none"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class AuthorStatusEnum(str, Enum):
    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class RoleEnum(str, Enum):
    GUEST = "guest"
    READER = "reader"
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
    following: List[str] = []
    followers_count: int = 0
    badges: List[str] = []
    is_premium: bool = False
    wallet_balance: int = 0
    is_shadowbanned: bool = False
    permissions: List[str] = []
    donation_link: Optional[str] = None
    kyc_status: KYCStatusEnum = KYCStatusEnum.NONE
    author_status: AuthorStatusEnum = AuthorStatusEnum.NONE
    is_verified: bool = False
    tos_accepted_at: Optional[datetime] = None
    welcome_message: Optional[str] = None
    blocked_users: List[str] = []

class UserCreate(UserBase):
    password: str
    agreed_to_terms: bool = False

class UserInDB(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    read_streak: int = 0
    last_read_date: Optional[datetime] = None
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    is_kyc_verified: bool = False
    passkeys: List[Dict[str, Any]] = []

class UserResponse(UserBase):
    id: str = Field(alias="_id")
    created_at: datetime
    
    class Config:
        populate_by_name = True
