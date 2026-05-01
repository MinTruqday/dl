from typing import Any
from fastapi import APIRouter, Depends
from models.user import UserInDB, RoleEnum
from api.dependencies import require_role, get_current_user
from core.response import APIResponse
from services.admin import AdminService
from services.audit import AuditService
from services.user_management import UserManagementService
from services.system_maintenance import SystemMaintenanceService
from services.marketing import MarketingService
from services.security import SecurityService
from services.moderation import ModerationService
from services.document import DocumentService
from pydantic import BaseModel

router = APIRouter(prefix="/admin")

class ReviewAuthorRequest(BaseModel):
    status: str
    reason: str = ""

class UpdateRoleRequest(BaseModel):
    role: str

class UpdateStatusRequest(BaseModel):
    is_active: bool

class BackupRequest(BaseModel):
    action: str

class MarketingCampaignRequest(BaseModel):
    title: str
    target_audience: str
    discount_percent: int

class MaintenanceRequest(BaseModel):
    enabled: bool
    message: str = ""

class ApiKeyRequest(BaseModel):
    name: str
    provider: str
    key_value: str

@router.get("/audit", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_audit_logs(limit: int = 50, offset: int = 0):
    return APIResponse(
        data=await AuditService.get_audit_logs(limit, offset), 
        message="Lấy nhật ký hệ thống thành công."
    )

@router.get("/users", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_all_users(limit: int = 50, offset: int = 0):
    return APIResponse(
        data=await UserManagementService.get_all_users(limit, offset), 
        message="Lấy danh sách người dùng thành công."
    )

@router.put("/users/{user_id}/role", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def update_user_role(user_id: str, req: UpdateRoleRequest):
    return APIResponse(
        data=await UserManagementService.update_user_role(user_id, req.role), 
        message="Cập nhật quyền thành công."
    )

@router.put("/users/{user_id}/status", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def update_user_status(user_id: str, req: UpdateStatusRequest):
    return APIResponse(
        data=await UserManagementService.update_user_status(user_id, req.is_active), 
        message="Cập nhật trạng thái tài khoản thành công."
    )

@router.get("/applications/authors", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_author_applications(status: str = "PENDING"):
    return APIResponse(
        data=await UserManagementService.get_author_applications(status), 
        message="Lấy danh sách đơn ứng tuyển thành công."
    )

@router.put("/applications/authors/{application_id}/review", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def review_author(application_id: str, req: ReviewAuthorRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await UserManagementService.review_author_application(application_id, req.status, req.reason, str(current_user.id)), 
        message="Xử lý đơn ứng tuyển thành công."
    )

@router.get("/stats", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_stats():
    return APIResponse(
        data=await AdminService.get_stats(), 
        message="Lấy thống kê thành công."
    )

@router.post("/backup", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def trigger_backup(req: BackupRequest):
    return APIResponse(
        data=await SystemMaintenanceService.trigger_backup(req.action), 
        message="Khởi tạo sao lưu thành công."
    )

@router.post("/marketing", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_marketing_campaign(req: MarketingCampaignRequest):
    return APIResponse(
        data=await MarketingService.create_marketing_campaign(req.title, req.target_audience, req.discount_percent), 
        message="Tạo chiến dịch marketing thành công."
    )

@router.get("/sys-health", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_sys_health():
    return APIResponse(
        data=await SystemMaintenanceService.get_sys_health(), 
        message="Kiểm tra hệ thống thành công."
    )

@router.post("/maintenance", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def toggle_maintenance(req: MaintenanceRequest):
    return APIResponse(
        data=await SystemMaintenanceService.toggle_maintenance_mode(req.enabled, req.message), 
        message="Cập nhật chế độ bảo trì thành công."
    )

@router.post("/api-keys", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_api_key(req: ApiKeyRequest):
    return APIResponse(
        data=await SystemMaintenanceService.create_api_key(req.name, req.provider, req.key_value), 
        message="Lưu API Key thành công."
    )

@router.get("/banners", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_banners():
    return APIResponse(
        data=await MarketingService.get_banners(), 
        message="Lấy danh sách banner thành công."
    )

@router.get("/security", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_security_config():
    return APIResponse(
        data=await SecurityService.get_security_config(), 
        message="Lấy cấu hình bảo mật thành công."
    )

@router.put("/security", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def update_security_config(data: dict):
    return APIResponse(
        data=await SecurityService.update_security_config(data), 
        message="Cập nhật cấu hình bảo mật thành công."
    )
