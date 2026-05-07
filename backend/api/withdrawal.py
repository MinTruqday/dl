from typing import Any
from fastapi import APIRouter, Depends
from api.dependency import require_role, get_current_user
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.withdrawal import WithdrawalService
from models.withdrawal import WithdrawalRequest
from pydantic import BaseModel

router = APIRouter(prefix="/rut-tien")

@router.post("/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def request_withdrawal(data: WithdrawalRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await WithdrawalService.request_withdrawal(data.model_dump(), current_user),
        message="Yêu cầu rút tiền thành công",
        status=201
    )

@router.get("/hang-doi/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_withdrawal_queue(status: str = "PENDING"):
    return APIResponse(
        data=await WithdrawalService.get_withdrawal_queue(status),
        message="Lấy hàng đợi thanh toán thành công"
    )

@router.post("/{withdrawal_id}/xac-thuc/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def verify_withdrawal(withdrawal_id: str, action: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await WithdrawalService.verify_withdrawal(withdrawal_id, action, current_user),
        message="Xử lý thanh toán thành công"
    )

@router.post("/{withdrawal_id}/huy-bo", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def cancel_withdrawal(withdrawal_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await WithdrawalService.cancel_withdrawal(withdrawal_id, current_user),
        message="Hủy yêu cầu rút tiền thành công"
    )

@router.get("/ca-nhan/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def get_my_withdrawals(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await WithdrawalService.get_my_withdrawals(current_user),
        message="Lấy danh sách yêu cầu rút tiền thành công"
    )
