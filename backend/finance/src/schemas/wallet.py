from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from uuid6 import uuid7

class TransactionType(str, Enum):
    TOPUP = "topup"
    PURCHASE = "purchase"
    RECEIVE = "receive"
    WITHDRAW = "withdraw"
    TIP = "tip"
    REFUND = "refund"
    TRANSFER_OUT = "transfer_out"
    TRANSFER_IN = "transfer_in"

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


class TransferRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipient_identifier: str = Field(min_length=1, max_length=320)
    amount: int = Field(gt=0, le=1000000000)
    note: str = Field(default="", max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=200)


class RecipientVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipient_identifier: str = Field(min_length=1, max_length=320)
