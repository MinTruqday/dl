from typing import Any

from fastapi import APIRouter, Depends, Query
from src.services.wallet import AccountLedger

from core.system_dependency import get_current_user, get_db
from core.api_response import APIResponse
from core.system_dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/vi-tien")


@router.get("/so-du", response_model=APIResponse[Any])
async def get_my_wallet(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await AccountLedger.get_wallet_balance(str(current_user.id), db=db),
        message="Lấy số dư tài khoản thành công",
        status=200,
    )


@router.get("/giao-dich", response_model=APIResponse[Any])
async def get_my_transactions(
    limit: int = Query(20),
    offset: int = Query(0),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AccountLedger.get_transactions(
            str(current_user.id), limit, offset, db=db
        ),
        message="Lấy lịch sử giao dịch thành công",
        status=200,
    )
