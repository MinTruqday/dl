from typing import Any

from core.dependency import get_current_user, get_db
from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends, Query
from src.services.wallet import WalletService

router = APIRouter(prefix="/wallets")


@router.get("/balance", response_model=APIResponse[Any])
async def get_my_wallet(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await WalletService.get_wallet_balance(str(current_user.id), db=db),
        message="Lấy số dư tài khoản thành công",
        status=200,
    )


@router.get("/transactions", response_model=APIResponse[Any])
async def get_my_transactions(
    limit: int = Query(20),
    offset: int = Query(0),
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await WalletService.get_transactions(
            str(current_user.id), limit, offset, db=db
        ),
        message="Lấy lịch sử giao dịch thành công",
        status=200,
    )