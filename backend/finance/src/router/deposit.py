from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.services.deposit import DepositManager

from core.dependency import get_current_user, get_db
from core.response import APIResponse
from core.schemas.user import UserInDB

router = APIRouter(prefix="/nap-tien")


class DepositRequest(BaseModel):
    amount: float
    payment_method: str = "PAYOS"


@router.post("", response_model=APIResponse[Any])
async def create_deposit(
    req: DepositRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DepositManager.create_deposit(
            req.amount, req.payment_method, current_user, db=db
        ),
        message="Đã khởi tạo giao dịch nạp tiền, đang chờ xác nhận",
        status=201,
    )
