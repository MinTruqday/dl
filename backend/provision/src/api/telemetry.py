from typing import Any
from fastapi import APIRouter, Depends
from src.api.dependency import get_db, require_role, get_current_user
from src.schemas.user import UserInDB, RoleEnum
from src.core.response import APIResponse
from src.services.telemetry import TelemetryService

router = APIRouter(prefix='/do-luong')

@router.get('/thong-ke', response_model=APIResponse[Any])
async def get_stats(
    current_user: UserInDB = Depends(require_role([RoleEnum.ADMIN])),
    db=Depends(get_db)
):
    return APIResponse(data=await TelemetryService.get_system_stats(db=db), message='Lấy thống kê hệ thống thành công')

@router.get('/suc-khoe-he-thong', response_model=APIResponse[Any])
async def get_sys_health(
    current_user: UserInDB = Depends(require_role([RoleEnum.ADMIN])),
    db=Depends(get_db)
):
    return APIResponse(data=await TelemetryService.get_sys_health(db=db), message='Kiểm tra sức khỏe hệ thống thành công')

@router.get('/hoat-dong-he-thong', response_model=APIResponse[Any])
async def get_activity_stats(
    days: int = 30,
    current_user: UserInDB = Depends(require_role([RoleEnum.ADMIN])),
    db=Depends(get_db)
):
    return APIResponse(data=await TelemetryService.get_activity_stats(days=days, db=db), message='Lấy nhật ký hệ thống thành công')

@router.get('/hoat-dong', response_model=APIResponse[Any])
async def get_moderator_activity(
    current_user: UserInDB = Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN])),
    db=Depends(get_db)
):
    return APIResponse(data=await TelemetryService.get_moderator_activity_log(str(current_user.id), db=db), message='Lấy nhật ký hoạt động điều hành thành công')