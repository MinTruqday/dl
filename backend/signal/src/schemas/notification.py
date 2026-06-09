from pydantic import BaseModel
from typing import Optional


class NotificationSettingsUpdate(BaseModel):
    enable_comment_notifications: bool = True
    enable_mention_notifications: bool = True
    enable_system_notifications: bool = True
    enable_email_digest: bool = False


class NewsletterRequest(BaseModel):
    email: str
