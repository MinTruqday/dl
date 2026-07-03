from pydantic import BaseModel

class DepositRequest(BaseModel):
    amount: float
    payment_method: str = "PAYOS"
