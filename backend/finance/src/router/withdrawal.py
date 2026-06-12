from typing import Any
from fastapi import APIRouter, Depends
from src.api.dependency import get_db, require_role, get_current_user
from src.schemas.user import UserInDB, RoleEnum
from core.response import APIResponse
from src.services.withdrawal import WithdrawalService
from src.schemas.withdrawal import WithdrawalRequest

router = APIRouter(prefix='/rut-tien')

@router.post('', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def request_withdrawal(data: WithdrawalRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await WithdrawalService.request_withdrawal(data.model_dump(), current_user, db=db), message='Yêu cầu rút tiền hoàn tất', status=201)

@router.get('/hang-doi', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_withdrawal_queue(status: str='PENDING', db=Depends(get_db)):
    return APIResponse(data=await WithdrawalService.get_withdrawal_queue(status, db=db), message='Lấy hàng đợi thanh toán hoàn tất')

@router.post('/{withdrawal_id}/xac-thuc', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def verify_withdrawal(withdrawal_id: str, action: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await WithdrawalService.verify_withdrawal(withdrawal_id, action, current_user, db=db), message='Xử lý thanh toán hoàn tất')

@router.post('/{withdrawal_id}/huy-bo', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def cancel_withdrawal(withdrawal_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await WithdrawalService.cancel_withdrawal(withdrawal_id, current_user, db=db), message='Hủy yêu cầu rút tiền hoàn tất')

@router.get('/ca-nhan', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def get_my_withdrawals(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await WithdrawalService.get_my_withdrawals(current_user, db=db), message='Lấy danh sách yêu cầu rút tiền hoàn tất')