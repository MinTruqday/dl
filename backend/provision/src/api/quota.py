from fastapi import APIRouter, Depends, HTTPException
from src.api.dependency import get_db, get_current_user, require_role
from core.schemas.user import UserInDB, RoleEnum
from core.schemas.quota import QuotaLimit
from src.services.quota import QuotaService
from core.response import APIResponse
from typing import Any

router = APIRouter(prefix='/han-muc')

@router.get('/kiem-tra', response_model=APIResponse[Any], include_in_schema=False)
async def check_quota_internal(user_id: str, role: str, db=Depends(get_db)):
    await QuotaService.check_quota(user_id, role, db=db)
    return APIResponse(data=None, message='Trong hạn mức', status=200)

@router.get('/me', response_model=APIResponse[Any])
async def get_my_quota(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    usage = await QuotaService.get_current_usage(str(current_user.id), current_user.role.value, db=db)
    return APIResponse(data=usage, message='Đã tải thông tin hạn mức')

@router.put('/config/{role}', response_model=APIResponse[Any])
async def update_role_quota(role: str, limits: QuotaLimit, current_user: UserInDB=Depends(require_role([RoleEnum.ADMIN])), db=Depends(get_db)):
    result = await QuotaService.update_global_limits(role, limits, db=db)
    return APIResponse(data=result, message='Đã cập nhật cấu hình hạn mức')

@router.get('/config', response_model=APIResponse[Any])
async def get_global_config(current_user: UserInDB=Depends(require_role([RoleEnum.ADMIN])), db=Depends(get_db)):
    config = await QuotaService._get_global_config(db=db)
    return APIResponse(data=config.role_limits, message='Đã tải cấu hình hạn mức')
