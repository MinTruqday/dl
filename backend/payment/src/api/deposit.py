from typing import Any

from fastapi import APIRouter, Depends, Request
from src.schemas.deposit import DepositRequest
from src.services.deposit import DepositService

from src.core.dependency import get_current_user, get_db
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(prefix="/nap-tien")



@router.post("", response_model=APIResponse[Any])
async def create_deposit(
    req: DepositRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DepositService.create_deposit_link(
            req, current_user, db=db
        ),
        message="Đã khởi tạo giao dịch nạp tiền, đang chờ xác nhận",
        status=201,
    )
