from typing import Any
from core.config import settings
from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends, Query
from src.services.telemetry import TelemetryService

router = APIRouter(prefix="/telemetry")

@router.get("/stats", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_stats(db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_system_stats(db=db),
        message="Comprehensive system performance statistics have been successfully generated and retrieved",
    )

@router.get("/health", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_sys_health(db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_sys_health(db=db),
        message="System health diagnostic check has been successfully completed and recorded",
    )

@router.get("/audit", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_audit_logs(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), offset: int = 0, db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_activity_stats(days=30, db=db),
        message="Internal system activity logs have been successfully compiled and retrieved",
    )

@router.get("/activity", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_activity(current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_activity_log(str(current_user.id), db=db),
        message="Administrative moderation activity logs have been successfully retrieved from database",
    )