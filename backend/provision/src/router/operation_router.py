from typing import Any, List, Optional

from core.response import APIResponse
from core.schemas.collector import CollectionRequest
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends, status
from src.router.dependency_router import get_current_user, get_db, require_role
from src.schemas.operation_schema import CampaignRequest
from src.services.operation_service import OperationService
from src.services.user_service import UserService

router = APIRouter(prefix="/operations")


@router.get(
    "/metrics",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_system_metrics(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_system_telemetry(db=db),
        message="Lấy dữ liệu hoạt động thành công",
    )


@router.get(
    "/maintenance",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_maintenance_status(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_maintenance_mode(db=db),
        message="Lấy trạng thái bảo trì hệ thống thành công",
    )


@router.post(
    "/maintenance",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def toggle_maintenance(enabled: bool, db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.toggle_maintenance_mode(enabled, db=db),
        message="Cập nhật cấu hình bảo trì hệ thống thành công",
    )


@router.post(
    "/backup",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def trigger_backup(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.trigger_backup(db=db),
        message="Bắt đầu quá trình sao lưu dữ liệu hệ thống",
    )


@router.post(
    "/api-key",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def create_api_key(name: str, db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.create_api_key(name, db=db),
        message="Tạo khóa bảo mật ứng dụng thành công",
    )


@router.post(
    "/marketing/campaign",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def create_marketing_campaign(payload: CampaignRequest, db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.create_marketing_campaign(
            payload.model_dump(), db=db
        ),
        message="Thiết lập chiến dịch quảng cáo thành công",
        status=201,
    )


@router.get(
    "/settings",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_system_config(db=Depends(get_db)):
    return APIResponse(data={}, message="Lấy cấu hình hệ thống thành công")


@router.get(
    "/health",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_system_health(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_system_health(db=db),
        message="Tạo báo cáo tình trạng hệ thống thành công",
    )


@router.get(
    "/reports",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_admin_reports(db=Depends(get_db)):
    return APIResponse(
        data=await UserService.get_report_queue(status_filter=None, db=db),
        message="Lấy danh sách báo cáo vi phạm thành công",
    )


@router.get(
    "/collectors/stats",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_collector_stats(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_collector_stats(db=db),
        message="Biên dịch dữ liệu thống kê thành công",
    )


@router.post(
    "/collectors/trigger",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def trigger_collection(req: CollectionRequest, db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.trigger_collection(req.source, req.pages, db=db),
        message="Bắt đầu quá trình thu thập dữ liệu",
    )


@router.post(
    "/collectors/stop",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def stop_collection(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.stop_collection(db=db),
        message="Gửi lệnh dừng thu thập dữ liệu thành công",
    )


@router.get(
    "/collectors/logs",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_collector_logs(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_collector_logs(db=db),
        message="Lấy nhật ký hoạt động thành công",
    )


@router.get(
    "/collectors/active-jobs",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_active_collector_jobs(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_active_collector_jobs(db=db),
        message="Lấy danh sách tác vụ chạy nền thành công",
    )


@router.post(
    "/users/{user_id}/shadowban",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def shadowban_user(
    payload: Any, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await OperationService.bulk_update_shadowban(
            payload.user_ids, payload.status, current_user, db=db
        ),
        message="Áp dụng quyền hiển thị thành công",
    )


@router.post(
    "/users/{user_id}/kyc/{status}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def verify_kyc(
    payload: Any, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await OperationService.bulk_verify_kyc(
            payload.user_ids, payload.status, current_user, db=db
        ),
        message="Cập nhật hồ sơ xác minh danh tính thành công",
    )


@router.get(
    "/storage/stats",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_minio_stats(db=Depends(get_db)):
    return APIResponse(
        data=await OperationService.get_minio_stats(db=db),
        message="Lấy thống kê sử dụng lưu trữ thành công",
    )