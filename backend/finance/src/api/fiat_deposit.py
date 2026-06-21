from typing import Any

from fastapi import APIRouter, Depends, Request
from src.schemas.fiat_deposit import DepositRequest
from src.services.deposit import FiatDeposit

from core.system_dependency import get_current_user, get_db
from core.api_response import APIResponse
from core.system_dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/nap-tien")



@router.post("", response_model=APIResponse[Any])
async def create_deposit(
    req: DepositRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await FiatDeposit.create_deposit(
            req.amount, req.payment_method, current_user, db=db
        ),
        message="Đã khởi tạo giao dịch nạp tiền, đang chờ xác nhận",
        status=201,
    )
