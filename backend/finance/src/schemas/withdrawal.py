from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WithdrawalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class BankInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bank_code: str = Field(
        default="OTHER",
        min_length=2,
        max_length=20,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    bank_name: str = Field(min_length=2, max_length=100)
    account_number: str = Field(min_length=6, max_length=34, pattern=r"^[A-Za-z0-9]+$")
    account_name: str = Field(min_length=2, max_length=100)

    @field_validator("bank_code", "bank_name", "account_number", "account_name")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return " ".join(value.strip().split())


class WithdrawalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: int = Field(ge=50, le=20_000_000)
    bank_info: BankInfo
    note: Optional[str] = Field(default=None, max_length=500)


class WithdrawalInDB(WithdrawalRequest):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    status: WithdrawalStatus = WithdrawalStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    rejection_reason: Optional[str] = None
import uuid
