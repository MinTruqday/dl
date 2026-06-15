from typing import Optional
from pydantic import BaseModel

class CampaignRequest(BaseModel):
    title: str
    target: str = "ALL"
    discount: int = 0

class BannerRequest(BaseModel):
    title: str
    image_url: str
    target_url: Optional[str] = None
    is_active: bool = True

class ConsumeQuotaRequest(BaseModel):
    user_id: str
    feature: str = "chat"
    req_reset_hours: int = 24
    tokens: int = 0

class InternalCreateUserRequest(BaseModel):
    email: str
    password_hash: Optional[str] = None
    full_name: str
    role: str = "READER"
    slug: str