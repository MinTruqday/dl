from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from uuid6 import uuid7
from enum import Enum

class TransactionType(str, Enum):
    TOPUP = "topup"
    PURCHASE = "purchase"
    RECEIVE = "receive"
    WITHDRAW = "withdraw"
    TIP = "tip"
    SUBSCRIPTION = "subscription"
    REFUND = "refund"

class CouponTargetType(str, Enum):
    ALL = "all"
    NEW_USER = "new_user"
    SUBSCRIBER = "subscriber"

class CouponStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

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

class Voucher(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    code: str
    amount_dl: int = Field(default=0, alias="amount_dl")
    is_used: bool = False
    used_by: Optional[str] = None
    used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True



class RedeemVoucherRequest(BaseModel):
    code: str

class PlanCreate(BaseModel):
    name: str
    description: str
    price_dl: int
    benefits: List[str]

class DocumentPricingRequest(BaseModel):
    price_dl: int = 0
    is_drm_protected: bool = True

class FlashSaleRequest(BaseModel):
    price: int
    expires_at: str

class TopupRequest(BaseModel):
    amount: int = Field(..., gt=0)
    method: str = "payos"

class VoucherCreateRequest(BaseModel):
    code: str
    amount_dl: int = Field(..., gt=0)
    expires_at: datetime

class CouponCreateRequest(BaseModel):
    code: str
    discount_percent: int = 10
    max_uses: int = 100
    document_id: Optional[str] = None
    expires_at: Optional[str] = None
    target_type: CouponTargetType = CouponTargetType.ALL
