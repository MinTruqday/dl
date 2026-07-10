from src.core.dependency import CurrentUser
from typing import Any, List, Optional

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, status
from src.api.dependency import get_current_user, get_db, require_role
from src.services.health import HealthService
from src.services.telemetry import TelemetryService

from src.core.response import APIResponse
from src.core.dependency import Role

router = APIRouter(route_class=LoggingRoute, prefix="/van-hanh")

@router.get(
    "/chi-so",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_system_metrics(db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_system_stats(),
        message="Trích xuất dữ liệu giám sát hoạt động hoàn tất",
    )

@router.get(
    "/bao-tri",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_maintenance_status(db=Depends(get_db)):
    return APIResponse(
        data=await HealthService.get_maintenance_mode(),
        message="Trích xuất trạng thái bảo trì hệ thống hoàn tất",
    )

@router.post(
    "/bao-tri",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def toggle_maintenance(enabled: bool, db=Depends(get_db)):
    return APIResponse(
        data=await HealthService.toggle_maintenance_mode(enabled),
        message="Cập nhật cấu hình bảo trì hệ thống hoàn tất",
    )

@router.post(
    "/sao-luu",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def trigger_backup(db=Depends(get_db)):
    return APIResponse(
        data=await HealthService.trigger_backup(),
        message="Tiến trình sao lưu dữ liệu hệ thống đã được khởi động",
    )


@router.get(
    "/cai-dat",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_system_config(db=Depends(get_db)):
    return APIResponse(data={}, message="Trích xuất cấu hình hệ thống hoàn tất")

@router.get(
    "/tinh-trang",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_system_health(db=Depends(get_db)):
    return APIResponse(
        data=await HealthService.get_system_health(),
        message="Trích xuất báo cáo tình trạng hệ thống hoàn tất",
    )

@router.get(
    "/bao-cao",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_admin_reports(db=Depends(get_db)):
    return APIResponse(
        data=await AccountService.get_report_queue(status_filter=None),
        message="Trích xuất danh sách báo cáo vi phạm hoàn tất",
    )

@router.post(
    "/nguoi-dung/{user_id}/cam-ngam",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def shadowban_user(
    payload: Any, current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await HealthService.bulk_update_shadowban(
            payload.user_ids, payload.status, current_user
        ),
        message="Cập nhật quyền hiển thị nội dung hoàn tất",
    )

@router.post(
    "/nguoi-dung/{user_id}/xac-minh/{status}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def verify_kyc(
    payload: Any, current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await HealthService.bulk_verify_kyc(
            payload.user_ids, payload.status, current_user
        ),
        message="Cập nhật trạng thái hồ sơ xác minh danh tính hoàn tất",
    )

@router.get(
    "/luu-tru/thong-ke",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_minio_stats(db=Depends(get_db)):
    return APIResponse(
        data=await HealthService.get_minio_stats(),
        message="Trích xuất thống kê sử dụng không gian lưu trữ hoàn tất",
    )
