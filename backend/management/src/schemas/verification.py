from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional

class Creator(BaseModel):
    bio: Optional[str] = None
    social_links: dict = {}
    total_earnings: float = 0.0

class KYC(BaseModel):
    status: str = "pending"
    document_url: Optional[str] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
