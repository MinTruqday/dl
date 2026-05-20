from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class MessageBase(BaseModel):
    sender_id: str
    receiver_id: str
    content: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    reply_to_id: Optional[str] = None
    is_pinned: bool = False
    is_read: bool = False
    is_edited: bool = False
    is_recalled: bool = False
    reactions: List[dict] = []
    self_destruct_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class MessageCreate(BaseModel):
    receiver_id: str
    content: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    reply_to_id: Optional[str] = None

class MessageInDB(MessageBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MessageResponse(MessageInDB):
    id: str = Field(alias="_id")
    replied_message: Optional[dict] = None
    class Config:
        populate_by_name = True

class ConversationResponse(BaseModel):
    other_user_id: str
    other_user: Optional[dict] = None
    last_message: Optional[MessageResponse] = None
    pinned_messages: List[MessageResponse] = []
    unread_count: int = 0
