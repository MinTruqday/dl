from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Request
from src.schemas.deposit import DepositRequest
from src.services.deposit import DepositService

from src.core.dependency import get_current_user, get_db
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/nap-tien")

@router.post("", response_model=APIResponse[Any])
async def create_deposit(
    req: DepositRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DepositService.create_deposit_link(
            req, current_user
        ),
        message="Khởi tạo giao dịch nạp tiền hoàn tất, hệ thống đang chờ xác nhận",
        status=201,
    )

@router.get("/kiem-tra/{order_code}", response_model=APIResponse[Any])
async def verify_deposit(
    order_code: int,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DepositService.verify_deposit(order_code, current_user),
        message="Xác minh giao dịch nạp tiền hoàn tất",
        status=200,
    )
