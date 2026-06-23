from typing import Any

from fastapi import APIRouter, Depends, Request
from src.schemas.deposits import DepositRequest
from src.services.deposits import FiatDeposit

from shared.dependencies import get_current_user, get_db
from shared.responses import APIResponse
from shared.dependencies import CurrentUser, RoleEnum

router = APIRouter(prefix="/nap-tien")



@router.post("", response_model=APIResponse[Any])
async def create_deposit(
    req: DepositRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await FiatDeposit.create_deposit_link(
            req, current_user, db=db
        ),
        message="Đã khởi tạo giao dịch nạp tiền, đang chờ xác nhận",
        status=201,
    )
