from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid6 import uuid7

class KYCStatusEnum(str, Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class RoleEnum(str, Enum):
    GUEST = "guest"
    READER = "reader"
    POTENTIAL_AUTHOR = "potential_author"
    AUTHOR = "author"
    MODERATOR = "moderator"
    ADMIN = "admin"

class UserInDB(BaseModel):
    id: str = Field(alias="_id")
    role: RoleEnum = RoleEnum.READER
    full_name: Optional[str] = None

    class Config:
        populate_by_name = True

class UpdateRoleRequest(BaseModel):
    role: RoleEnum

class UpdateStatusRequest(BaseModel):
    is_active: bool

class ModerationActionRequest(BaseModel):
    reason: str
    duration_hours: Optional[int] = None

class NoteRequest(BaseModel):
    note: str
