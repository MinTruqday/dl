from typing import Any
from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from core.schemas.quota import QuotaLimit
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends
from src.schemas.management import ConsumeQuotaRequest
from src.services.quotas import QuotaService

router = APIRouter(prefix="/quotas")

@router.get("/check", response_model=APIResponse[Any], include_in_schema=False)
async def check_quota_internal(user_id: str, role: str, ai_tier: str = "BASIC", feature: str = "chat", db=Depends(get_db)):
    limits = await QuotaService.check_quota(user_id, role, ai_tier, feature, db=db)
    return APIResponse(
        data=limits.model_dump(),
        message="Requested operation is within allowed usage quota limits for this tier",
        status=200
    )

@router.get("/me", response_model=APIResponse[Any])
async def get_my_quota(current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    usage = await QuotaService.get_current_usage(str(current_user.id), current_user.role.value, current_user.ai_tier.value, db=db)
    return APIResponse(
        data=usage,
        message="Current resource usage quota information has been successfully retrieved from database"
    )

@router.put("/{role}/config", response_model=APIResponse[Any])
async def update_role_quota(role: str, limits: QuotaLimit, current_user: UserInDB = Depends(require_role([RoleEnum.ADMIN])), db=Depends(get_db)):
    await QuotaService.update_role_quota(role, limits.model_dump(), db=db)
    return APIResponse(
        data={},
        message="Global resource quota configuration has been successfully updated and applied"
    )

@router.get("/config", response_model=APIResponse[Any])
async def get_global_config(current_user: UserInDB = Depends(require_role([RoleEnum.ADMIN])), db=Depends(get_db)):
    global_cfg = await QuotaService.get_global_config_from_db(db=db)
    return APIResponse(
        data=global_cfg,
        message="Global resource quota configuration settings have been successfully retrieved"
    )

@router.post("/consume", response_model=APIResponse[Any], include_in_schema=False)
async def consume_quota(req: ConsumeQuotaRequest, db=Depends(get_db)):
    await QuotaService.consume_request(req.user_id, req.feature, req.req_reset_hours, db=db)
    if req.tokens > 0:
        await QuotaService.consume_tokens(req.user_id, req.tokens, req.feature, req.req_reset_hours, db=db)
    return APIResponse(
        data=None,
        message="Requested amount of resource quota successfully consumed from allocated limits",
        status=200
    )