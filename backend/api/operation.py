from typing import Any, List, Optional
from fastapi import APIRouter, Depends, status
from models.user import UserInDB, RoleEnum
from api.dependency import require_role, get_current_user
from core.response import APIResponse
from services.operation import OperationService
from services.payout import PayoutService
from services.user import UserService

router = APIRouter(prefix="/van-hanh")

@router.get("/chi-so", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_metrics():
    return APIResponse(
        data=await OperationService.get_system_health(), 
        message="Lấy thông số hệ thống thành công"
    )

@router.get("/bao-tri", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_maintenance_status():
    return APIResponse(
        data=await OperationService.get_maintenance_mode(),
        message="Lấy trạng thái bảo trì thành công"
    )

@router.post("/bao-tri", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def toggle_maintenance(enabled: bool):
    return APIResponse(
        data=await OperationService.toggle_maintenance_mode(enabled), 
        message="Cập nhật trạng thái bảo trì thành công"
    )

@router.get("/rut-tien", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_payouts_list(status: str = "PENDING"):
    return APIResponse(
        data=await PayoutService.get_payout_queue(status),
        message="Lấy danh sách thanh toán thành công"
    )

@router.post("/sao-luu", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def trigger_backup():
    return APIResponse(
        data=await OperationService.trigger_backup(), 
        message="Đã khởi tạo quá trình sao lưu hệ thống"
    )

@router.post("/khoa-api", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_api_key(name: str):
    return APIResponse(
        data=await OperationService.create_api_key(name), 
        message="Tạo khóa API thành công"
    )

@router.post("/tiep-thi/chien-dich", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_marketing_campaign(data: dict):
    return APIResponse(
        data=await OperationService.create_marketing_campaign(data), 
        message="Khởi tạo chiến dịch tiếp thị thành công"
    )

@router.get("/don-ung-tuyen/tac-gia", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_author_applications(status: str = "PENDING"):
    return APIResponse(
        data=await OperationService.get_author_applications(status),
        message="Lấy danh sách đơn ứng tuyển thành công"
    )

@router.put("/don-ung-tuyen/tac-gia/{application_id}/xet-duyet", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def review_author_application(application_id: str, data: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await OperationService.review_author_application(application_id, data["status"], data.get("reason", ""), str(current_user.id)),
        message="Xử lý đơn ứng tuyển thành công"
    )

@router.get("/cau-hinh", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_config():
    return APIResponse(data={}, message="Lấy cấu hình hệ thống thành công")

@router.get("/suc-khoe-he-thong", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_health():
    return APIResponse(
        data=await OperationService.get_system_health(), 
        message="Lấy trạng thái hệ thống thành công"
    )

@router.get("/bao-cao", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_admin_reports():
    return APIResponse(
        data=await UserService.get_report_queue(status_filter=None), 
        message="Lấy danh sách báo cáo thành công"
    )

@router.get("/thu-thap/thong-ke", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_collector_stats():
    return APIResponse(
        data=await OperationService.get_collector_stats(),
        message="Lấy thông số thu thập thành công"
    )

@router.post("/nguoi-dung/{user_id}/shadowban", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def shadowban_user(user_id: str, is_banned: bool, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await UserService.shadowban_user(user_id, is_banned, current_user),
        message="Cập nhật shadowban thành công"
    )

@router.post("/nguoi-dung/{user_id}/kyc/{status}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def verify_kyc(user_id: str, status: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await UserService.verify_kyc(user_id, status, current_user),
        message="Xử lý KYC thành công"
    )

