from src.core.dependency import CurrentUser
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, status
from src.api.dependency import get_current_user, get_db, require_role
from src.schemas.health import CampaignRequest
from src.services.health import HealthService
from src.services.telemetry import TelemetryService
from src.services.account import AccountService

from src.core.response import APIResponse
from src.schemas.account import Role, UserInDB

router = APIRouter(prefix="/van-hanh")


@router.get(
    "/chi-so",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_system_metrics(db=Depends(get_db)):
    return APIResponse(
        data=await TelemetryService.get_system_stats(db=db),
        message="Lấy dữ liệu hoạt động thành công",
    )


@router.get(
    "/bao-tri",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_maintenance_status(db=Depends(get_db)):
    return APIResponse(
        data=await HealthService.get_maintenance_mode(db=db),
        message="Lấy trạng thái bảo trì thành công",
    )


@router.post(
    "/bao-tri",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def toggle_maintenance(enabled: bool, db=Depends(get_db)):
    return APIResponse(
        data=await HealthService.toggle_maintenance_mode(enabled, db=db),
        message="Cập nhật cấu hình bảo trì thành công",
    )


@router.post(
    "/sao-luu",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def trigger_backup(db=Depends(get_db)):
    return APIResponse(
        data=await HealthService.trigger_backup(db=db),
        message="Bắt đầu sao lưu dữ liệu",
    )


@router.post(
    "/tiep-thi/chien-dich",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def create_marketing_campaign(payload: CampaignRequest, db=Depends(get_db)):
    return APIResponse(
        data=await HealthService.create_marketing_campaign(
            payload.model_dump(), db=db
        ),
        message="Thiết lập chiến dịch quảng cáo thành công",
        status=201,
    )


@router.get(
    "/cai-dat",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_system_config(db=Depends(get_db)):
    return APIResponse(data={}, message="Lấy cấu hình thành công")


@router.get(
    "/tinh-trang",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_system_health(db=Depends(get_db)):
    return APIResponse(
        data=await HealthService.get_system_health(db=db),
        message="Tạo báo cáo tình trạng thành công",
    )


@router.get(
    "/bao-cao",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_admin_reports(db=Depends(get_db)):
    return APIResponse(
        data=await AccountService.get_report_queue(status_filter=None, db=db),
        message="Lấy danh sách báo cáo vi phạm thành công",
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
            payload.user_ids, payload.status, current_user, db=db
        ),
        message="Áp dụng quyền hiển thị thành công",
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
            payload.user_ids, payload.status, current_user, db=db
        ),
        message="Cập nhật hồ sơ xác minh danh tính thành công",
    )


@router.get(
    "/luu-tru/thong-ke",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_minio_stats(db=Depends(get_db)):
    return APIResponse(
        data=await HealthService.get_minio_stats(db=db),
        message="Lấy thống kê sử dụng lưu trữ thành công",
    )
