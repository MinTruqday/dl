from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from uuid6 import uuid7

class TransactionType(str, Enum):
    TOPUP = "topup"
    PURCHASE = "purchase"
    RECEIVE = "receive"
    WITHDRAW = "withdraw"
    TIP = "tip"
    REFUND = "refund"

class CouponTargetType(str, Enum):
    ALL = "all"
    NEW_USER = "new_user"

class CouponStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class WithdrawalStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"

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

class Coupon(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid7()), alias="_id")
    code: str
    amount_dl: int = Field(default=0, alias="amount_dl")
    is_used: bool = False
    used_by: Optional[str] = None
    used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True

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

class DepositRequest(BaseModel):
    amount: float
    payment_method: str = "PAYOS"

class PurchaseRequest(BaseModel):
    document_id: str
    coupon_code: Optional[str] = None

class MembershipRequest(BaseModel):
    tier: str

class CouponCreateRequest(BaseModel):
    code: str
    discount_percent: float
    max_uses: int
    expires_at: Optional[str] = None
    document_id: Optional[str] = None
    target_type: CouponTargetType = CouponTargetType.ALL

class RedeemCouponRequest(BaseModel):
    code: str

class DocumentPricingRequest(BaseModel):
    price_dl: int = 0
    is_drm_protected: bool = True