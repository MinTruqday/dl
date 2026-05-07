from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
class BannerBase(BaseModel):
    title: str
    description: Optional[str] = ""
    image_url: str
    link_url: Optional[str] = ""
    is_active: bool = True
    order: int = 0
    bg_color: Optional[str] = "bg-black"
    text_color: Optional[str] = "text-white"
class BannerCreate(BannerBase):
    pass
class BannerUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None
    bg_color: Optional[str] = None
    text_color: Optional[str] = None
class BannerInDB(BannerBase):
    id: str
    created_at: datetime
    updated_at: datetime
