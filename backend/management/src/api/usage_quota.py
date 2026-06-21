from core.system_dependency import CurrentUser
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from src.api.system_dependency import get_current_user, get_db, require_role
from src.services.usage_quota import UsageQuota

from core.api_response import APIResponse
from src.schemas.usage_quota import QuotaLimit, ConsumeQuotaRequest
from src.schemas.user_profile import RoleEnum, UserInDB

router = APIRouter(prefix="/han-muc")


@router.get("/kiem-tra", response_model=APIResponse[Any], include_in_schema=False)
async def check_quota_internal(
    user_id: str,
    role: str,
    ai_tier: str = "BASIC",
    feature: str = "chat",
    db=Depends(get_db),
):
    limits = await UsageQuota.check_quota(user_id, role, ai_tier, feature, db=db)
    return APIResponse(
        data=limits.model_dump(),
        message="Thao tác nằm trong giới hạn sử dụng cho phép",
        status=200,
    )


@router.get("/ca-nhan", response_model=APIResponse[Any])
async def get_my_quota(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    
    role = getattr(current_user.role, "value", current_user.role)
    ai_tier = getattr(current_user, "ai_tier", "BASIC")
    if hasattr(ai_tier, "value"):
        ai_tier = ai_tier.value
        
    usage = await UsageQuota.get_current_usage(
        str(current_user.id), role, ai_tier, db=db
    )
    return APIResponse(data=usage, message="Lấy thông tin hạn mức sử dụng thành công")


@router.put("/{role}/cau-hinh", response_model=APIResponse[Any])
async def update_role_quota(
    role: str,
    limits: QuotaLimit,
    current_user: CurrentUser = Depends(require_role([RoleEnum.ADMIN])),
    db=Depends(get_db),
):
    await UsageQuota.update_role_quota(role, limits.model_dump(), db=db)
    return APIResponse(
        data={},
        message="Cập nhật giới hạn tài nguyên thành công",
    )


@router.get("/cau-hinh", response_model=APIResponse[Any])
async def get_global_config(
    current_user: CurrentUser = Depends(require_role([RoleEnum.ADMIN])), db=Depends(get_db)
):
    global_cfg = await UsageQuota.get_global_config_from_db(db=db)
    return APIResponse(
        data=global_cfg,
        message="Lấy cấu hình tài nguyên thành công",
    )





@router.post("/tieu-thu", response_model=APIResponse[Any], include_in_schema=False)
async def consume_quota(req: ConsumeQuotaRequest, db=Depends(get_db)):
    await UsageQuota.consume_request(
        req.user_id, req.feature, req.req_reset_hours, db=db
    )
    if req.tokens > 0:
        await UsageQuota.consume_tokens(
            req.user_id, req.tokens, req.feature, req.req_reset_hours, db=db
        )
    return APIResponse(
        data=None, message="Sử dụng dung lượng tài nguyên thành công", status=200
    )
