from typing import Any

from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends, Query
from src.router.dependency import get_current_user, get_db, require_role
from src.services.telemetry import TelemetryService
from core.config import settings

router = APIRouter(prefix="/telemetry")


@router.get(
    "/stats",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_stats(db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_system_stats(db=db),
        message="Lấy thống kê hiệu suất thành công",
    )


@router.get(
    "/health",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_sys_health(db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_sys_health(db=db),
        message="Hoàn tất kiểm tra",
    )


@router.get(
    "/audit",
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
        message="Lấy nhật ký thành công",
    )


@router.get(
    "/activity",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_activity(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await TelemetryService.get_activity_log(
            str(current_user.id), db=db
        ),
        message="Lấy nhật ký kiểm duyệt thành công",
    )