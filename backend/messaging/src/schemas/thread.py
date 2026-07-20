import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field
from uuid6 import uuid7

class Base(BaseModel):
    sender_id: str
    receiver_id: str
    content: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    attachments: Optional[List[dict]] = []
    reply_to_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    thread_count: int = 0
    client_msg_id: Optional[str] = None
    is_pinned: bool = False
    is_read: bool = False
    is_edited: bool = False
    is_recalled: bool = False
    reactions: List[dict] = []
    self_destruct_seconds: Optional[int] = None
    self_destruct_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Creation(BaseModel):
    receiver_id: str
    client_msg_id: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    attachments: Optional[List[dict]] = []
    reply_to_id: Optional[str] = None
    parent_message_id: Optional[str] = None

class Record(Base):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Response(Record):
    id: str = Field(alias="_id")
    replied_message: Optional[dict] = None

    class Config:
        populate_by_name = True

class Conversation(BaseModel):
    other_user_id: str
    other_user: Optional[dict] = None
    last_message: Optional[Response] = None
    pinned_messages: List[Response] = []
    unread_count: int = 0
