from typing import Any
from fastapi import APIRouter, Depends, Request
from core.response import APIResponse
from api.dependency import get_current_user
from models.user import UserInDB
from models.wallet import TopupRequest
from services.gateway import GatewayService

router = APIRouter(prefix="/cong-thanh-toan")


@router.post("/tao-link", response_model=APIResponse[Any])
async def create_payment_link(req: TopupRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await GatewayService.create_payment_link(req, current_user),
        message="Khởi tạo liên kết thanh toán thành công",
        status=201,
    )


@router.post("/payos/webhook")
async def payos_webhook(request: Request):
    return await GatewayService.payos_webhook(request)


@router.get("/kiem-tra/{order_code}", response_model=APIResponse[Any])
async def verify_payment(order_code: int, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await GatewayService.verify_payment(order_code),
        message="Kiểm tra trạng thái thanh toán",
        status=200,
    )
