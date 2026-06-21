from typing import Optional
from pydantic import BaseModel

class BannerRequest(BaseModel):
    title: str
    image_url: str
    target_url: Optional[str] = None
    is_active: bool = True
