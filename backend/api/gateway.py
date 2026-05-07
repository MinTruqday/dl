from typing import Any
from shared.core.response import APIResponse
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from api.dependency import get_current_user
from shared.models.user import UserInDB
from services.gateway import GatewayService

router = APIRouter(prefix="/cong-thanh-toan")

class TopupRequest(BaseModel):
    amount: int 

@router.post("/momo/tao-moi", response_model=APIResponse[Any])
async def create_momo_payment(req: TopupRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await GatewayService.create_momo_payment(req, current_user), message="Khởi tạo giao dịch MoMo thành công", status=201)

@router.post("/momo/ipn", response_model=APIResponse[Any])
async def momo_ipn(request: Request):
    return APIResponse(data=await GatewayService.momo_ipn(request), message="Xử lý thông báo thanh toán MoMo thành công", status=200)
