from typing import Any

from core.dependency import get_current_user, get_db
from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends, Request
from src.schemas.wallet_schema import TopupRequest
from src.services.deposit_service import DepositService

router = APIRouter(prefix="/deposit")


@router.post("/create-link", response_model=APIResponse[Any])
async def create_deposit_link(
    req: TopupRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DepositService.create_deposit_link(
            req.model_dump(), current_user, db=db
        ),
        message="Đã tạo liên kết nạp tiền",
        status=201,
    )


@router.post("/payos/webhook")
async def payos_webhook(request: Request, db=Depends(get_db)):
    return await DepositService.deposit_webhook(request, db=db)


@router.get("/check/{order_code}", response_model=APIResponse[Any])
async def verify_deposit(
    order_code: int,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DepositService.verify_deposit(order_code, current_user, db=db),
        message="Kiểm tra trạng thái nạp tiền",
        status=200,
    )
