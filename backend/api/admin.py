from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from models.user import UserInDB, RoleEnum
from api.dependencies import require_role, get_current_user
from services.admin import AdminService
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/admin")

class ReviewAuthorRequest(BaseModel):
    status: str
    reason: str = ""

class UpdateRoleRequest(BaseModel):
    role: RoleEnum

class UpdateStatusRequest(BaseModel):
    is_active: bool

class BackupRequest(BaseModel):
    action: str

class MarketingCampaignRequest(BaseModel):
    title: str
    target_audience: str
    discount_percent: int

class AutomationFlowRequest(BaseModel):
    trigger: str
    action: str

class MaintenanceRequest(BaseModel):
    enabled: bool
    message: str = ""

class ApiKeyRequest(BaseModel):
    name: str
    provider: str
    key_value: str

@router.get("/audit", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_audit_logs(limit: int = 50, offset: int = 0):
    return APIResponse(data=await AdminService.get_audit_logs(limit, offset), message="Lấy nhật ký hệ thống thành công.", status=200)

@router.get("/users", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_all_users(limit: int = 50, offset: int = 0):
    return APIResponse(data=await AdminService.get_all_users(limit, offset), message="Lấy danh sách người dùng thành công.", status=200)

@router.put("/users/{user_id}/role", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def update_user_role(user_id: str, req: UpdateRoleRequest):
    return APIResponse(data=await AdminService.update_user_role(user_id, req.role), message="Cập nhật quyền người dùng thành công.", status=200)

@router.put("/users/{user_id}/shadowban", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def toggle_shadowban(user_id: str, is_shadowbanned: bool):
    return APIResponse(data=await AdminService.toggle_shadowban(user_id, is_shadowbanned), message="Cập nhật trạng thái Shadowban thành công.", status=200)

@router.put("/users/{user_id}/status", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def update_user_status(user_id: str, req: UpdateStatusRequest):
    return APIResponse(data=await AdminService.update_user_status(user_id, req.is_active), message="Cập nhật trạng thái tài khoản thành công.", status=200)

@router.get("/applications/authors", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_author_applications(status: str = "PENDING"):
    return APIResponse(data=await AdminService.get_author_applications(status), message="Lấy danh sách đơn đăng ký tác giả thành công.", status=200)

@router.put("/applications/authors/{application_id}/review", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def review_author(application_id: str, req: ReviewAuthorRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await AdminService.review_author_application(application_id, req.status, req.reason, str(current_user.id)), message="Phê duyệt/Từ chối đơn đăng ký tác giả thành công.", status=200)

@router.get("/stats", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_stats():
    return APIResponse(data=await AdminService.get_stats(), message="Lấy số liệu thống kê quản trị thành công.", status=200)

@router.get("/config", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_config():
    return APIResponse(data=await AdminService.get_config(), message="Lấy cấu hình hệ thống thành công.", status=200)

@router.put("/config", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def update_config(req: dict):
    return APIResponse(data=await AdminService.update_config(req), message="Cập nhật cấu hình hệ thống thành công.", status=200)

@router.post("/backup", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def trigger_backup(req: BackupRequest):
    return APIResponse(data=await AdminService.trigger_backup(req.action), message="Thực hiện sao lưu dữ liệu thành công.", status=200)

@router.get("/trends", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_big_data_trends():
    return APIResponse(data=await AdminService.get_big_data_trends(), message="Lấy dữ liệu xu hướng hệ thống thành công.", status=200)

@router.get("/storage", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_storage_stats():
    return APIResponse(data=await AdminService.get_storage_stats(), message="Lấy số liệu lưu trữ thành công.", status=200)

@router.post("/marketing", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_marketing_campaign(req: MarketingCampaignRequest):
    return APIResponse(data=await AdminService.create_marketing_campaign(req.title, req.target_audience, req.discount_percent), message="Tạo chiến dịch Marketing thành công.", status=200)

@router.get("/decision-support", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_decision_support():
    return APIResponse(data=await AdminService.get_decision_support(), message="Lấy dữ liệu hỗ trợ quyết định thành công.", status=200)

@router.get("/sys-health", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_sys_health():
    return APIResponse(data=await AdminService.get_sys_health(), message="Kiểm tra sức khỏe hệ thống thành công.", status=200)

@router.get("/docker-health", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_docker_health():
    return APIResponse(data=await AdminService.get_docker_health(), message="Kiểm tra trạng thái Docker thành công.", status=200)

@router.get("/ai-infrastructure", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_ai_infrastructure():
    return APIResponse(data=await AdminService.get_ai_gateway_stats(), message="Lấy số liệu hạ tầng AI thành công.", status=200)

@router.post("/maintenance", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def toggle_maintenance(req: MaintenanceRequest):
    return APIResponse(data=await AdminService.toggle_maintenance_mode(req.enabled, req.message), message="Cập nhật chế độ bảo trì thành công.", status=200)

@router.get("/maintenance", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_maintenance_mode():
    return APIResponse(data=await AdminService.get_maintenance_mode(), message="Lấy trạng thái bảo trì thành công.", status=200)

@router.get("/api-keys", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_api_keys():
    return APIResponse(data=await AdminService.manage_api_keys(), message="Lấy danh sách API Key thành công.", status=200)

@router.post("/api-keys", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_api_key(req: ApiKeyRequest):
    return APIResponse(data=await AdminService.create_api_key(req.name, req.provider, req.key_value), message="Tạo API Key mới thành công.", status=200)

@router.get("/banners", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_banners():
    return APIResponse(data=await AdminService.get_banners(), message="Lấy danh sách Banner quảng cáo thành công.", status=200)

@router.post("/banners", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_banner(data: dict):
    return APIResponse(data=await AdminService.create_banner(data), message="Tạo Banner mới thành công.", status=200)

@router.put("/banners/{banner_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def update_banner(banner_id: str, data: dict):
    return APIResponse(data=await AdminService.update_banner(banner_id, data), message="Cập nhật Banner thành công.", status=200)

@router.delete("/banners/{banner_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def delete_banner(banner_id: str):
    return APIResponse(data=await AdminService.delete_banner(banner_id), message="Xóa Banner thành công.", status=200)

@router.get("/security", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_security_config():
    return APIResponse(data=await AdminService.get_security_config(), message="Lấy cấu hình bảo mật thành công.", status=200)

@router.put("/security", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def update_security_config(data: dict):
    return APIResponse(data=await AdminService.update_security_config(data), message="Cập nhật cấu hình bảo mật thành công.", status=200)
