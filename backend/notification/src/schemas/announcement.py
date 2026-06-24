from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from uuid6 import uuid7


class AnnouncementCreate(BaseModel):
    target_user_id: str
    title: str
    body: str
    type: str = "system"


class Announcement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    target_user_id: str
    title: str
    body: str
    is_read: bool = False
    type: str = "system"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
