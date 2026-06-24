from typing import Any

from fastapi import APIRouter, Depends, Query
from src.services.wallet import WalletService
from src.schemas.wallet import RedeemCouponRequest

from shared.dependency import get_current_user, get_db
from shared.response import APIResponse
from shared.dependency import CurrentUser, Role

router = APIRouter(prefix="/vi-dien-tu")


@router.get("/so-du", response_model=APIResponse[Any])
async def get_my_wallet(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await WalletService.get_balance(current_user, db=db),
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
            current_user, limit=limit, skip=offset, db=db
        ),
        message="Lấy lịch sử giao dịch thành công",
        status=200,
    )


@router.post("/doi-ma-qua-tang", response_model=APIResponse[Any])
async def redeem_coupon(
    req: RedeemCouponRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await WalletService.redeem_coupon(req, current_user, db=db),
        message="Đổi mã quà tặng thành công",
        status=200,
    )
