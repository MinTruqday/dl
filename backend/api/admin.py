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

@router.get("/audit", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_audit_logs(limit: int = 50, offset: int = 0):
    return await AdminService.get_audit_logs(limit, offset)

@router.get("/users", dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_all_users(limit: int = 50, offset: int = 0):
    return await AdminService.get_all_users(limit, offset)

@router.put("/users/{user_id}/role", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def update_user_role(user_id: str, req: UpdateRoleRequest):
    return await AdminService.update_user_role(user_id, req.role)

@router.put("/users/{user_id}/shadowban", dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def toggle_shadowban(user_id: str, is_shadowbanned: bool):
    return await AdminService.toggle_shadowban(user_id, is_shadowbanned)

@router.put("/users/{user_id}/status", dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def update_user_status(user_id: str, req: UpdateStatusRequest):
    return await AdminService.update_user_status(user_id, req.is_active)

@router.get("/applications/authors", dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_author_applications(status: str = "PENDING"):
    return await AdminService.get_author_applications(status)

@router.put("/applications/authors/{application_id}/review", dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def review_author(application_id: str, req: ReviewAuthorRequest, current_user: UserInDB = Depends(get_current_user)):
    return await AdminService.review_author_application(application_id, req.status, req.reason, str(current_user.id))

@router.get("/stats", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_stats():
    return await AdminService.get_stats()

@router.get("/config", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_config():
    return await AdminService.get_config()

@router.put("/config", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def update_config(req: dict):
    return await AdminService.update_config(req)

@router.post("/backup", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def trigger_backup(req: BackupRequest):
    return await AdminService.trigger_backup(req.action)

@router.get("/trends", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_big_data_trends():
    return await AdminService.get_big_data_trends()

@router.get("/storage", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_storage_stats():
    return await AdminService.get_storage_stats()

@router.post("/marketing", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_marketing_campaign(req: MarketingCampaignRequest):
    return await AdminService.create_marketing_campaign(req.title, req.target_audience, req.discount_percent)

@router.get("/decision-support", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_decision_support():
    return await AdminService.get_decision_support()

@router.get("/sys-health", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_sys_health():
    return await AdminService.get_sys_health()

@router.get("/docker-health", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_docker_health():
    return await AdminService.get_docker_health()

@router.get("/ai-infrastructure", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_ai_infrastructure():
    return await AdminService.get_ai_gateway_stats()

@router.post("/maintenance", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def toggle_maintenance(req: MaintenanceRequest):
    return await AdminService.toggle_maintenance_mode(req.enabled, req.message)

@router.get("/maintenance", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_maintenance_mode():
    return await AdminService.get_maintenance_mode()

@router.get("/api-keys", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_api_keys():
    return await AdminService.manage_api_keys()

@router.post("/api-keys", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_api_key(req: ApiKeyRequest):
    return await AdminService.create_api_key(req.name, req.provider, req.key_value)

@router.get("/banners", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_banners():
    return await AdminService.get_banners()

@router.post("/banners", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def create_banner(data: dict):
    return await AdminService.create_banner(data)

@router.put("/banners/{banner_id}", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def update_banner(banner_id: str, data: dict):
    return await AdminService.update_banner(banner_id, data)

@router.delete("/banners/{banner_id}", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def delete_banner(banner_id: str):
    return await AdminService.delete_banner(banner_id)

@router.get("/security", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_security_config():
    return await AdminService.get_security_config()

@router.put("/security", dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def update_security_config(data: dict):
    return await AdminService.update_security_config(data)
