from typing import Any, List, Optional
from fastapi import APIRouter, Depends, status
from models.user import UserInDB, RoleEnum
from api.dependency import require_role, get_current_user
from core.response import APIResponse
from services.administration import AdministrationService
from services.payout import PayoutService

router = APIRouter()

@router.get("/metrics/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_metrics():
    return APIResponse(
        data=await AdministrationService.get_system_health(), 
        message="Lấy thông số hệ thống thành công."
    )

@router.get("/maintenance/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_maintenance_status():
    return APIResponse(
        data={"enabled": False}, # Placeholder
        message="Lấy trạng thái bảo trì thành công."
    )

@router.post("/maintenance/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def toggle_maintenance(enabled: bool):
    return APIResponse(
        data=await AdministrationService.toggle_maintenance_mode(enabled), 
        message="Cập nhật trạng thái bảo trì thành công."
    )

@router.get("/payouts/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_payouts_list(status: str = "PENDING"):
    return APIResponse(
        data=await PayoutService.get_payout_queue(status),
        message="Lấy danh sách thanh toán thành công."
    )

@router.post("/backup/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def trigger_backup():
    return APIResponse(
        data=await AdministrationService.trigger_backup(), 
        message="Đã khởi tạo quá trình sao lưu hệ thống."
    )

@router.post("/api-keys/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_api_key(name: str):
    return APIResponse(
        data=await AdministrationService.create_api_key(name), 
        message="Tạo khóa API thành công."
    )

@router.post("/marketing/campaigns/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_marketing_campaign(data: dict):
    return APIResponse(
        data=await AdministrationService.create_marketing_campaign(data), 
        message="Khởi tạo chiến dịch tiếp thị thành công."
    )
@router.get("/applications/authors/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_author_applications(status: str = "PENDING"):
    return APIResponse(
        data=await AdministrationService.get_author_applications(status),
        message="Lấy danh sách đơn ứng tuyển thành công."
    )

@router.put("/applications/authors/{application_id}/review/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def review_author_application(application_id: str, data: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await AdministrationService.review_author_application(application_id, data["status"], data.get("reason", ""), str(current_user.id)),
        message="Xử lý đơn ứng tuyển thành công."
    )

@router.get("/config/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_config():
    # Placeholder logic
    return APIResponse(data={}, message="Lấy cấu hình hệ thống thành công.")

@router.get("/sys-health/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_health():
    return APIResponse(
        data=await AdministrationService.get_system_health(), 
        message="Lấy trạng thái hệ thống thành công."
    )

@router.get("/maintenance/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_maintenance_status():
    return APIResponse(
        data=await AdministrationService.get_maintenance_mode(),
        message="Lấy trạng thái bảo trì thành công."
    )

@router.get("/payouts/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_payouts_list(status: str = "PENDING"):
    return APIResponse(
        data=await PayoutService.get_payout_queue(status),
        message="Lấy danh sách thanh toán thành công."
    )

@router.get("/reports/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_admin_reports():
    from services.moderation import ModerationService
    return APIResponse(
        data=await ModerationService.get_report_queue(status_filter=None), 
        message="Lấy danh sách báo cáo thành công."
    )

@router.get("/collector/stats/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_collector_stats():
    return APIResponse(
        data=await AdministrationService.get_collector_stats(),
        message="Lấy thông số thu thập thành công."
    )
