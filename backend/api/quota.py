from fastapi import APIRouter, Depends, HTTPException
from api.dependency import get_db, get_current_user, require_role
from models.user import UserInDB, RoleEnum
from models.quota import QuotaLimit
from services.quota import QuotaService
from core.response import APIResponse
from typing import Any
router = APIRouter(prefix='/quota', tags=['Quota'])

@router.get('/me', response_model=APIResponse[Any])
async def get_my_quota(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    usage = await QuotaService.get_current_usage(str(current_user.id), current_user.role.value, db=db)
    return APIResponse(data=usage, message='Lấy thông tin hạn mức thành công')

@router.put('/config/{role}', response_model=APIResponse[Any])
async def update_role_quota(role: str, limits: QuotaLimit, current_user: UserInDB=Depends(require_role([RoleEnum.ADMIN])), db=Depends(get_db)):
    result = await QuotaService.update_global_limits(role, limits, db=db)
    return APIResponse(data=result, message='Cập nhật cấu hình hạn mức thành công')

@router.get('/config', response_model=APIResponse[Any])
async def get_global_config(current_user: UserInDB=Depends(require_role([RoleEnum.ADMIN])), db=Depends(get_db)):
    config = await QuotaService._get_global_config(db=db)
    return APIResponse(data=config.role_limits, message='Lấy cấu hình hạn mức thành công')