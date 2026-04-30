from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from enum import Enum

class PrivacyEnum(str, Enum):
    PUBLIC = "public"
    CLOSE_FRIENDS = "close_friends"
    PRIVATE = "private"
    FOLLOWERS = "followers"

class ItemTypeEnum(str, Enum):
    POST = "post"
    QUOTE = "quote"
    REVIEW = "review"

class FollowBase(BaseModel):
    follower_id: str
    following_id: str

class FollowCreate(FollowBase):
    pass

class FollowInDB(FollowBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FollowResponse(FollowBase):
    id: str = Field(alias="_id")
    created_at: datetime
    class Config:
        populate_by_name = True

class QuoteCardBase(BaseModel):
    user_id: str
    document_id: str
    document_slug: str
    document_title: str
    quote_text: str
    background_color: str = "#ffffff"
    font_style: str = "serif"
    likes_count: int = 0
    comments_count: int = 0

class QuoteCardCreate(BaseModel):
    document_id: str
    quote_text: str
    background_color: Optional[str] = "#ffffff"
    font_style: Optional[str] = "serif"

class QuoteCardInDB(QuoteCardBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class QuoteCardResponse(QuoteCardBase):
    id: str = Field(alias="_id")
    created_at: datetime
    class Config:
        populate_by_name = True

class FeedItemResponse(BaseModel):
    id: str
    item_type: str
    actor: Dict[str, Any]
    content: Dict[str, Any]
    created_at: datetime
    reactions: Dict[str, int] = {}
    user_reaction: Optional[str] = None

class NotificationBase(BaseModel):
    user_id: str
    type: str
    message: str
    is_read: bool = False
    link: Optional[str] = None

class NotificationCreate(NotificationBase):
    pass

class NotificationInDB(NotificationBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationResponse(NotificationBase):
    id: str = Field(alias="_id")
    created_at: datetime
    class Config:
        populate_by_name = True

class PollOption(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    votes: int = 0

class StatusUpdateCreate(BaseModel):
    content: str
    poll_options: Optional[List[str]] = None
    attached_document_id: Optional[str] = None
    attached_document_title: Optional[str] = None
    media_urls: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    location: Optional[str] = None
    feeling: Optional[str] = None
    mentions: Optional[List[str]] = None
    privacy: PrivacyEnum = PrivacyEnum.PUBLIC
    comment_privacy: PrivacyEnum = PrivacyEnum.PUBLIC
    is_premium: bool = False
    price: int = 0
    read_progress: Optional[int] = None
    item_type: ItemTypeEnum = ItemTypeEnum.POST
    quote_text: Optional[str] = None
    bg_color: Optional[str] = None
    font_style: Optional[str] = None
    repost_post_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None

class StatusUpdateInDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    content: str
    poll_options: Optional[List[PollOption]] = []
    voter_ids: Dict[str, str] = {}
    attached_document_id: Optional[str] = None
    attached_document_title: Optional[str] = None
    media_urls: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    location: Optional[str] = None
    feeling: Optional[str] = None
    mentions: Optional[List[str]] = []
    privacy: PrivacyEnum = PrivacyEnum.PUBLIC
    edit_history: List[Dict[str, Any]] = []
    is_hidden_by: List[str] = []
    is_shadowbanned: bool = False
    reported_by: List[Dict[str, Any]] = []
    saved_by: List[str] = []
    comment_privacy: PrivacyEnum = PrivacyEnum.PUBLIC
    view_count: int = 0
    is_pinned: bool = False
    is_premium: bool = False
    price: int = 0
    paid_by: List[str] = []
    read_progress: Optional[int] = None
    item_type: ItemTypeEnum = ItemTypeEnum.POST
    quote_text: Optional[str] = None
    bg_color: Optional[str] = None
    font_style: Optional[str] = None
    repost_post_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    reactions: Dict[str, int] = {}
    reaction_users: Dict[str, List[str]] = {}

class PollVoteRequest(BaseModel):
    option_index: int

class StatusResponse(StatusUpdateInDB):
    id: str = Field(alias="_id")
    user_reaction: Optional[str] = None
    user: Optional[Dict] = None
    class Config:
        populate_by_name = True

class StoryCreate(BaseModel):
    media_url: Optional[str] = None
    text_content: Optional[str] = None
    background_color: str = "#18181b"
    font_style: Optional[str] = "sans"
    text_color: Optional[str] = "#ffffff"
    stickers: Optional[List[Dict[str, Any]]] = []
    privacy: str = "public"
    link_url: Optional[str] = None
    link_text: Optional[str] = None
    poll_data: Optional[Dict[str, Any]] = None
    quiz_data: Optional[Dict[str, Any]] = None
    mentions: Optional[List[str]] = []

class StoryView(BaseModel):
    user_id: str
    viewed_at: datetime = Field(default_factory=datetime.utcnow)

class StoryInDB(StoryCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    is_highlight: bool = False
    is_archived: bool = False
    reactions: Dict[str, int] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    viewers: List[StoryView] = []

class StoryResponse(StoryInDB):
    id: str = Field(alias="_id")
    user: Optional[Dict] = None
    has_unread: bool = True
    class Config:
        populate_by_name = True
