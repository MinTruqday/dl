import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field
from uuid6 import uuid7

class TransactionType(str, Enum):
    TOPUP = "topup"
    PURCHASE = "purchase"
    RECEIVE = "receive"
    WITHDRAW = "withdraw"
    TIP = "tip"
    REFUND = "refund"



class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    user_id: str
    type: TransactionType
    amount: int
    reference_id: Optional[str] = None
    note: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PurchaseRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    user_id: str
    item_type: str = "document"
    item_id: str
    price_paid: int
    purchased_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))



class DocumentPricingRequest(BaseModel):
    price_dl: int = 0
    is_drm_protected: bool = True

class TopupRequest(BaseModel):
    amount: int = Field(gt=0)
    method: str = "payos"
