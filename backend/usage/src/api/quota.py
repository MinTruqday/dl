from src.core.dependency import CurrentUser
from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, HTTPException
from src.core.dependency import get_current_user, get_db, require_role
from src.services.quota import QuotaService

from src.core.response import APIResponse
from src.schemas.quota import QuotaLimit, ConsumeQuotaRequest
from src.core.dependency import Role

router = APIRouter(route_class=LoggingRoute, prefix="/han-muc")

@router.get("/kiem-tra", response_model=APIResponse[Any], include_in_schema=False)
async def check_quota_internal(
    user_id: str,
    role: str,
    ai_tier: str = "BASIC",
    feature: str = "chat",
    db=Depends(get_db),
):
    limits = await QuotaService.check_quota(user_id, role, ai_tier, feature)
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
        
    usage = await QuotaService.get_current_usage(
        str(current_user.id), role, ai_tier
    )
    return APIResponse(data=usage, message="Lấy thông tin hạn mức sử dụng thành công")

@router.put("/{role}/cau-hinh", response_model=APIResponse[Any])
async def update_role_quota(
    role: str,
    limits: QuotaLimit,
    current_user: CurrentUser = Depends(require_role([Role.ADMIN])),
    db=Depends(get_db),
):
    await QuotaService.update_role_quota(role, limits.model_dump())
    return APIResponse(
        data={},
        message="Cập nhật giới hạn tài nguyên thành công",
    )

@router.get("/cau-hinh", response_model=APIResponse[Any])
async def get_global_config(
    current_user: CurrentUser = Depends(require_role([Role.ADMIN])), db=Depends(get_db)
):
    global_cfg = await QuotaService.get_global_config_from_db()
    return APIResponse(
        data=global_cfg,
        message="Lấy cấu hình tài nguyên thành công",
    )

@router.post("/tieu-thu", response_model=APIResponse[Any], include_in_schema=False)
async def consume_quota(req: ConsumeQuotaRequest, db=Depends(get_db)):
    await QuotaService.consume_request(
        req.user_id, req.feature, req.req_reset_hours
    )
    if req.tokens > 0:
        await QuotaService.consume_tokens(
            req.user_id, req.tokens, req.feature, req.req_reset_hours
        )
    return APIResponse(
        data=None, message="Sử dụng dung lượng tài nguyên thành công", status=200
    )

from src.schemas.quota import ConsumeUploadQuotaRequest

@router.get("/tai-len/xac-minh", response_model=APIResponse[Any], include_in_schema=False)
async def check_upload_quota_internal(
    item_type: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    role = getattr(current_user.role, "value", current_user.role)
    ai_tier = getattr(current_user, "ai_tier", "BASIC")
    if hasattr(ai_tier, "value"):
        ai_tier = ai_tier.value
        
    await QuotaService.check_upload_quota(str(current_user.id), role, ai_tier, item_type)
    return APIResponse(
        data=None,
        message="Dung lượng tải lên hợp lệ",
        status=200,
    )

@router.post("/tai-len/tieu-thu", response_model=APIResponse[Any], include_in_schema=False)
async def consume_upload_quota_internal(
    req: ConsumeUploadQuotaRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db)
):
    await QuotaService.consume_upload_quota(
        str(current_user.id), req.item_type, req.req_reset_hours
    )
    return APIResponse(
        data=None, message="Sử dụng dung lượng tải lên thành công", status=200
    )
