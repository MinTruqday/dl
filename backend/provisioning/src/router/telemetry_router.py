from typing import Any

from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends, Query
from src.router.dependency_router import get_current_user, get_db, require_role
from src.services.telemetry_service import TelemetryService
from core.config import settings

router = APIRouter(prefix="/telemetry")


@router.get(
    "/thong-ke",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_stats(db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_system_stats(db=db),
        message="The comprehensive system performance statistics have been successfully generated and retrieved",
    )


@router.get(
    "/suc-khoe-he-thong",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_sys_health(db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_sys_health(db=db),
        message="The system health diagnostic check has been successfully completed",
    )


@router.get(
    "/kiem-tra",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_audit_logs(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    offset: int = 0,
    db=Depends(get_db),
):
    return APIResponse(
        data=await TelemetryService.get_activity_stats(days=30, db=db),
        message="The internal system activity logs have been successfully compiled and retrieved",
    )


@router.get(
    "/hoat-dong",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def get_moderator_activity(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await TelemetryService.get_moderator_activity_log(
            str(current_user.id), db=db
        ),
        message="The administrative moderation activity logs have been successfully retrieved",
    )