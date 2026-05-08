from typing import Any
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from core.response import APIResponse
from api.dependency import get_current_user
from models.user import UserInDB
from models.wallet import TopupRequest, CouponCreateRequest
from services.gateway import GatewayService

router = APIRouter(prefix="/cong-thanh-toan")

@router.post("/momo/tao-moi", response_model=APIResponse[Any])
async def create_momo_payment(req: TopupRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await GatewayService.create_momo_payment(req, current_user), message="Khởi tạo giao dịch MoMo thành công", status=201)

@router.post("/momo/ipn")
async def momo_ipn(request: Request):
    return await GatewayService.momo_ipn(request)
