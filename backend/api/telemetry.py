from typing import Any
from fastapi import APIRouter, Depends
from api.dependency import get_db, require_role, get_current_user
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.telemetry import TelemetryService
router = APIRouter(prefix='/do-luong')

@router.get('/thong-ke', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_stats(db=Depends(get_db)):
    return APIResponse(data=await TelemetryService.get_system_stats(db=db), message='Lấy thống kê hệ thống thành công')

@router.get('/suc-khoe-he-thong', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_sys_health(db=Depends(get_db)):
    return APIResponse(data=await TelemetryService.get_sys_health(db=db), message='Kiểm tra sức khỏe hệ thống thành công')

@router.get('/kiem-tra', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_audit_logs(limit: int=50, offset: int=0, db=Depends(get_db)):
    return APIResponse(data=await TelemetryService.get_activity_stats(days=30, db=db), message='Lấy nhật ký hệ thống thành công')

@router.get('/hoat-dong', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_moderator_activity(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await TelemetryService.get_moderator_activity_log(str(current_user.id), db=db), message='Lấy nhật ký hoạt động điều hành thành công')