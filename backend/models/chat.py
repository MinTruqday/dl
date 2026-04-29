from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

class MessageBase(BaseModel):
    sender_id: str
    receiver_id: str
    content: str
    is_read: bool = False

class MessageCreate(BaseModel):
    receiver_id: str
    content: str

class MessageInDB(MessageBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MessageResponse(MessageInDB):
    id: str = Field(alias="_id")
    class Config:
        populate_by_name = True

class ConversationResponse(BaseModel):
    other_user_id: str
    other_user: Optional[dict] = None
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0
