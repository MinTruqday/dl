import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field
from uuid6 import uuid7


class SeriesBase(BaseModel):
    title: str
    description: Optional[str] = ""
    document_ids: List[str] = []


class SeriesCreateRequest(SeriesBase):
    pass


class SeriesInDB(SeriesBase):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    author_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SeriesResponse(SeriesBase):
    id: str = Field(alias="_id")
    author_id: str
    created_at: datetime
    documents: Optional[List[dict]] = None

    class Config:
        populate_by_name = True
