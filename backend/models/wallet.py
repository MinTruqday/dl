from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid
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
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    type: TransactionType
    amount: int
    reference_id: Optional[str] = None
    note: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PurchaseRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    item_type: str = "chapter"
    item_id: str
    price_paid: int
    purchased_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Voucher(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    code: str
    amount_dl: int = Field(default=0, alias="amount_dl")
    is_used: bool = False
    used_by: Optional[str] = None
    used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True

class TipRequest(BaseModel):
    receiver_id: str
    amount: int
    message: Optional[str] = None

class WithdrawalRequest(BaseModel):
    amount: int
    payment_method: str
    account_info: str

class RedeemVoucherRequest(BaseModel):
    code: str

class UnlockRequest(BaseModel):
    item_id: str
    item_type: str = "chapter" # chapter, document

class VoteRequest(BaseModel):
    item_id: str
    item_type: str
    amount: int

class PlanCreate(BaseModel):
    name: str
    description: str
    price_dl: int
    benefits: List[str]

class DocumentPricingRequest(BaseModel):
    price_dl: int = 0
    is_drm_protected: bool = True

class FlashSaleRequest(BaseModel):
    price: float
    expires_at: str

class TopupRequest(BaseModel):
    amount: int
    method: str = "momo" # momo, vnpay, transfer

class VoucherCreateRequest(BaseModel):
    code: str
    amount_dl: int
    expires_at: datetime

class CouponCreateRequest(BaseModel):
    code: str
    discount_percent: int = 10
    max_uses: int = 100
    document_id: Optional[str] = None
    expires_at: Optional[str] = None
    target_type: CouponTargetType = CouponTargetType.ALL
