from core.dependency import CurrentUser
from typing import Any

from fastapi import APIRouter, Depends, Query
from src.router.dependency import get_current_user, get_db, require_role
from src.services.telemetry import TelemetryManager

from core.config import settings
from core.response import APIResponse
from src.schemas.user import RoleEnum, UserInDB

router = APIRouter(prefix="/giam-sat")


@router.get(
    "/thong-ke",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_stats(db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryManager.get_system_stats(db=db),
        message="Lấy thống kê hiệu suất thành công",
    )


@router.get(
    "/tinh-trang",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_sys_health(db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryManager.get_sys_health(db=db),
        message="Hoàn tất kiểm tra",
    )


@router.get(
    "/kiem-toan",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_audit_logs(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    offset: int = 0,
    db=Depends(get_db),
):
    return APIResponse(
        data=await TelemetryManager.get_activity_stats(days=30, db=db),
        message="Lấy nhật ký thành công",
    )


@router.get(
    "/hoat-dong",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_activity(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await TelemetryManager.get_activity_log(str(current_user.id), db=db),
        message="Lấy nhật ký kiểm duyệt thành công",
    )
