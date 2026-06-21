from typing import Any

from fastapi import APIRouter, Depends, Query
from src.services.account_ledger import AccountLedger
from src.schemas.account_ledger import RedeemCouponRequest

from core.system_dependency import get_current_user, get_db
from core.api_response import APIResponse
from core.system_dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/vi-tien")


@router.get("/so-du", response_model=APIResponse[Any])
async def get_my_wallet(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await AccountLedger.get_balance(current_user, db=db),
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
        data=await AccountLedger.get_history(
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
        data=await AccountLedger.redeem_coupon(req, current_user, db=db),
        message="Đổi mã quà tặng thành công",
        status=200,
    )
