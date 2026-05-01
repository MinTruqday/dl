from typing import Any
from fastapi import APIRouter, Depends
from api.dependencies import require_role
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.payout import PayoutService
from pydantic import BaseModel

router = APIRouter(prefix="/payouts")

class PayoutRequest(BaseModel):
    amount: int
    bank_info: dict

@router.post("", response_model=APIResponse[Any])
async def request_payout(data: PayoutRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await PayoutService.request_payout(data.model_dump(), current_user),
        message="Yêu cầu rút tiền đã được gửi.",
        status=201
    )

@router.get("", response_model=APIResponse[Any])
async def get_my_payouts(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await PayoutService.get_my_payouts(current_user),
        message="Lấy lịch sử rút tiền thành công."
    )
