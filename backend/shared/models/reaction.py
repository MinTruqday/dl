from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid
class ReactionBase(BaseModel):
    item_id: str
    item_type: str
    reaction_type: str
    user_id: str
class ReactionCreate(BaseModel):
    reaction_type: Optional[str] = None
    item_type: str
class ReactionInDB(ReactionBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
