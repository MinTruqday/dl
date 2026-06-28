from src.core.dependency import CurrentUser
from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Query
from src.api.dependency import get_current_user, get_db, require_role
from src.services.telemetry import TelemetryService

from src.core.infrastructure.configuration import settings
from src.core.response import APIResponse
from src.schemas.account import Role, UserInDB

router = APIRouter(route_class=LoggingRoute, prefix="/giam-sat")

@router.get(
    "/thong-ke",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_stats(db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_system_stats(),
        message="Lấy thống kê hiệu suất thành công",
    )

@router.get(
    "/tinh-trang",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_sys_health(db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_sys_health(),
        message="Hoàn tất kiểm tra",
    )

@router.get(
    "/kiem-toan",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_audit_logs(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    offset: int = 0,
    db=Depends(get_db),
):
    return APIResponse(
        data=await TelemetryService.get_activity_stats(days=30),
        message="Lấy nhật ký thành công",
    )

@router.get(
    "/hoat-dong",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_activity(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await TelemetryService.get_activity_log(str(current_user.id)),
        message="Lấy nhật ký kiểm duyệt thành công",
    )
