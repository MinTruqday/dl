from typing import Literal

from pydantic import BaseModel, Field

class DepositRequest(BaseModel):
    amount: int = Field(ge=1000, le=2_000_000_000)
    payment_method: Literal["PAYOS"] = "PAYOS"
