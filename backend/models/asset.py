from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

class AssetBase(BaseModel):
    filename: str
    type: str = "image"
    size_bytes: int = 0
    url: str = ""

class AssetUploadRequest(AssetBase):
    pass

class AssetInDB(AssetBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
