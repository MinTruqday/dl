from typing import Any
from fastapi import APIRouter, Depends
from api.dependency import require_role, get_current_user
from shared.models.user import UserInDB, RoleEnum
from shared.core.response import APIResponse
from services.payout import PayoutService
from pydantic import BaseModel

router = APIRouter(prefix="/rut-tien")

class PayoutRequest(BaseModel):
    amount: int
    bank_info: dict

@router.post("/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def request_payout(data: PayoutRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await PayoutService.request_payout(data.model_dump(), current_user),
        message="Yêu cầu rút tiền thành công",
        status=201
    )

@router.get("/hang-doi/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_payout_queue(status: str = "PENDING"):
    return APIResponse(
        data=await PayoutService.get_payout_queue(status),
        message="Lấy hàng đợi thanh toán thành công"
    )

@router.post("/{payout_id}/xac-thuc/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def verify_payout(payout_id: str, action: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await PayoutService.verify_payout(payout_id, action, current_user),
        message="Xử lý thanh toán thành công"
    )

@router.post("/{payout_id}/huy-bo", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def cancel_payout(payout_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await PayoutService.cancel_payout(payout_id, current_user),
        message="Hủy yêu cầu rút tiền thành công"
    )

@router.get("/ca-nhan/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def get_my_payouts(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await PayoutService.get_my_payouts(current_user),
        message="Lấy danh sách yêu cầu rút tiền thành công"
    )
