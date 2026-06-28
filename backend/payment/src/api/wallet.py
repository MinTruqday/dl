from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Query
from src.services.wallet import WalletService

from src.core.dependency import get_current_user, get_db
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/vi-dien-tu")

@router.get("/so-du", response_model=APIResponse[Any])
async def get_my_wallet(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await WalletService.get_balance(current_user),
        message="Lấy số dư tài khoản thành công",
        status=200,
    )

@router.get("/lich-su", response_model=APIResponse[Any])
async def get_my_transactions(
    limit: int = Query(20),
    offset: int = Query(0),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await WalletService.get_history(
            current_user, limit=limit, skip=offset
        ),
        message="Lấy lịch sử giao dịch thành công",
        status=200,
    )
