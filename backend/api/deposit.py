from typing import Any
from fastapi import APIRouter, Depends, Request
from core.response import APIResponse
from api.dependency import get_current_user
from models.user import UserInDB
from models.wallet import TopupRequest
from services.deposit import DepositService

router = APIRouter(prefix="/nap-tien")


@router.post("/tao-link", response_model=APIResponse[Any])
async def create_deposit_link(req: TopupRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DepositService.create_deposit_link(req, current_user),
        message="Khởi tạo liên kết nạp tiền thành công",
        status=201,
    )


@router.post("/payos/webhook")
async def payos_webhook(request: Request):
    return await DepositService.deposit_webhook(request)


@router.get("/kiem-tra/{order_code}", response_model=APIResponse[Any])
async def verify_deposit(order_code: int, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DepositService.verify_deposit(order_code),
        message="Kiểm tra trạng thái nạp tiền",
        status=200,
    )
