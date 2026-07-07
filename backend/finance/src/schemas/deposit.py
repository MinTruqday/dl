from pydantic import BaseModel

class DepositRequest(BaseModel):
    amount: int
    payment_method: str = "PAYOS"
