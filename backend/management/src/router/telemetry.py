from typing import Any
from core.config import settings
from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from src.services.telemetry import TelemetryService

router = APIRouter(prefix="/do-luong")

@router.get("/thong-ke", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_stats(db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_system_stats(db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.get("/suc-khoe", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_sys_health(db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_sys_health(db=db),
        message="Kiểm tra sức khỏe hệ thống hoàn tất và ổn định",
    )

@router.get("/kiem-toan", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_audit_logs(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), offset: int = 0, db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_activity_stats(days=30, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.get("/hoat-dong", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_activity(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_activity_log(str(current_user.get("id")), db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )