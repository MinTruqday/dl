from typing import Any

from fastapi import APIRouter, Depends, Request
from src.schemas.deposit import DepositRequest
from src.services.deposit import DepositManager

from core.dependency import get_current_user, get_db
from core.response import APIResponse
from core.dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/nap-tien")



@router.post("", response_model=APIResponse[Any])
async def create_deposit(
    req: DepositRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DepositManager.create_deposit(
            req.amount, req.payment_method, current_user, db=db
        ),
        message="Đã khởi tạo giao dịch nạp tiền, đang chờ xác nhận",
        status=201,
    )
