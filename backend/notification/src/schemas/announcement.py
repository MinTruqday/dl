from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class AnnouncementCreate(BaseModel):
    target_user_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=2000)
    type: str = Field(default="system", min_length=1, max_length=50)
    idempotency_key: Optional[str] = Field(default=None, min_length=1, max_length=200)

class Announcement(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    target_user_id: str
    title: str
    body: str
    is_read: bool = False
    type: str = "system"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))



class AnnouncementSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enable_comment_notifications: bool = True
    enable_mention_notifications: bool = True
    enable_system_notifications: bool = True
    enable_email_digest: bool = False
import uuid
