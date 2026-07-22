from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field
from uuid6 import uuid7

class Base(BaseModel):
    sender_id: str
    receiver_id: str
    content: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    attachments: List[dict] = Field(default_factory=list)
    reply_to_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    thread_count: int = 0
    client_msg_id: Optional[str] = None
    is_pinned: bool = False
    is_read: bool = False
    is_edited: bool = False
    is_recalled: bool = False
    reactions: List[dict] = Field(default_factory=list)
    self_destruct_seconds: Optional[int] = None
    self_destruct_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    is_scheduled: bool = False
    updated_at: Optional[datetime] = None
    is_system: bool = False
    system_action: Optional[str] = None
    visible_to: Optional[List[str]] = None

class Creation(BaseModel):
    receiver_id: str = Field(min_length=1, max_length=128)
    client_msg_id: Optional[str] = Field(default=None, max_length=128)
    content: Optional[str] = Field(default=None, max_length=10000)
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    attachments: List[dict] = Field(default_factory=list, max_length=10)
    reply_to_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None

class Record(Base):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Response(Record):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    replied_message: Optional[dict] = None

class Conversation(BaseModel):
    other_user_id: str
    other_user: Optional[dict] = None
    last_message: Optional[Response] = None
    pinned_messages: List[Response] = Field(default_factory=list)
    unread_count: int = 0
