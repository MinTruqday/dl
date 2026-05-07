from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.dependency import get_current_user
from models.user import UserInDB
from services.payment import PaymentService

router = APIRouter()

@router.post("/deposit", response_model=APIResponse[Any])
async def deposit_fiat(amount_vnd: int, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PaymentService.deposit_fiat(amount_vnd, current_user), message="Yêu cầu nạp tiền đã được gửi.", status=200)
