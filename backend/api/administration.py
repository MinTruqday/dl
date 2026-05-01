from typing import Any, List, Optional
from fastapi import APIRouter, Depends, status
from models.user import UserInDB, RoleEnum
from api.dependency import require_role, get_current_user
from core.response import APIResponse
from services.administration import AdministrationService

router = APIRouter(prefix="/administration")

@router.get("/metrics", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_system_metrics():
    return APIResponse(
        data=await AdministrationService.get_system_metrics(), 
        message="Lấy thông số hệ thống thành công."
    )

@router.post("/maintenance", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def toggle_maintenance(enabled: bool):
    return APIResponse(
        data=await AdministrationService.toggle_maintenance_mode(enabled), 
        message="Cập nhật trạng thái bảo trì thành công."
    )

@router.post("/backup", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def trigger_backup():
    return APIResponse(
        data=await AdministrationService.trigger_backup(), 
        message="Đã khởi tạo quá trình sao lưu hệ thống."
    )

@router.post("/api-keys", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_api_key(name: str):
    return APIResponse(
        data=await AdministrationService.create_api_key(name), 
        message="Tạo khóa API thành công."
    )

@router.post("/marketing/campaigns", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_marketing_campaign(data: dict):
    return APIResponse(
        data=await AdministrationService.create_marketing_campaign(data), 
        message="Khởi tạo chiến dịch tiếp thị thành công."
    )
