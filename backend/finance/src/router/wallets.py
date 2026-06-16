from typing import Any
from core.dependency import get_current_user, get_db
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from src.services.wallets import WalletService

router = APIRouter(prefix="/vi-tien")

@router.get("/so-du", response_model=APIResponse[Any])
async def get_my_wallet(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await WalletService.get_balance(current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.get("/giao-dich", response_model=APIResponse[Any])
async def get_my_transactions(limit: int = Query(20), offset: int = Query(0), current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await WalletService.get_history(current_user, limit=limit, skip=offset, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )