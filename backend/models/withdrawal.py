from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from uuid6 import uuid7
from enum import Enum

class WithdrawalStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"

class WithdrawalRequest(BaseModel):
    amount: int = Field(..., gt=0)
    bank_info: str = Field(..., min_length=10)
    note: Optional[str] = None

class WithdrawalInDB(WithdrawalRequest):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    user_id: str
    status: WithdrawalStatus = WithdrawalStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    rejection_reason: Optional[str] = None
