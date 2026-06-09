from pydantic import BaseModel
from enum import Enum
from datetime import datetime, timezone
from typing import Optional
from uuid6 import uuid7
from pydantic import Field

class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    PURCHASE = "PURCHASE"
    REFUND = "REFUND"
    TIP = "TIP"
    REWARD = "REWARD"

class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    user_id: str
    type: TransactionType
    amount: int
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
