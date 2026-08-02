from src.core.dependency import CurrentUser
from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, HTTPException
from src.core.dependency import get_current_user, get_db, require_role, verify_internal_token
from src.services.quota import QuotaService

from src.core.response import APIResponse
from src.schemas.quota import QuotaLimit, ConsumeQuotaRequest
from src.core.dependency import Role

router = APIRouter(route_class=LoggingRoute, prefix="/han-muc")

@router.get("/xac-minh", response_model=APIResponse[Any], include_in_schema=False, dependencies=[Depends(verify_internal_token)])
async def check_quota_internal(
    user_id: str,
    role: str,
    ai_tier: str = "BASIC",
    feature: str = "chat",
    db=Depends(get_db),
):
    limits = await QuotaService.check_and_reserve_quota(user_id, role, ai_tier, feature)
    return APIResponse(
        data=limits.model_dump(),
        message="Xác minh giới hạn tài nguyên hoàn tất",
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
    return APIResponse(data=usage, message="Trích xuất thông tin hạn mức sử dụng tài nguyên hoàn tất")

@router.put("/cai-dat/{role}", response_model=APIResponse[Any])
async def update_role_quota(
    role: str,
    limits: QuotaLimit,
    current_user: CurrentUser = Depends(require_role([Role.ADMIN])),
    db=Depends(get_db),
):
    await QuotaService.update_role_quota(role, limits.model_dump(exclude_unset=True))
    return APIResponse(
        data={},
        message="Cập nhật cấu hình giới hạn tài nguyên hệ thống hoàn tất",
    )

@router.get("/cai-dat", response_model=APIResponse[Any])
async def get_global_config(
    current_user: CurrentUser = Depends(require_role([Role.ADMIN])), db=Depends(get_db)
):
    global_cfg = await QuotaService.get_global_config_from_db()
    return APIResponse(
        data=global_cfg,
        message="Trích xuất cấu hình tài nguyên hệ thống hoàn tất",
    )

@router.post("/su-dung", response_model=APIResponse[Any], include_in_schema=False, dependencies=[Depends(verify_internal_token)])
async def consume_quota(req: ConsumeQuotaRequest, db=Depends(get_db)):
    if any(
        value > 0
        for value in [
            req.tokens,
            req.input_tokens,
            req.output_tokens,
            req.cached_tokens,
            req.tool_tokens,
        ]
    ):
        await QuotaService.consume_tokens(
            req.user_id,
            req.tokens,
            req.feature,
            req.role,
            req.ai_tier,
            req.input_tokens,
            req.output_tokens,
            req.cached_tokens,
            req.tool_tokens,
        )
    return APIResponse(
        data=None, message="Ghi nhận mức tiêu thụ tài nguyên hệ thống hoàn tất", status=200
    )

from src.schemas.quota import UploadQuotaReservationRequest

@router.post("/tai-len/dat-cho", response_model=APIResponse[Any], include_in_schema=False)
async def reserve_upload_quota_internal(
    req: UploadQuotaReservationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    role = getattr(current_user.role, "value", current_user.role)
    ai_tier = getattr(current_user, "ai_tier", "BASIC")
    if hasattr(ai_tier, "value"):
        ai_tier = ai_tier.value

    reservation = await QuotaService.reserve_upload_quota(
        str(current_user.id),
        role,
        ai_tier,
        req.item_type.value,
        req.req_reset_hours,
    )
    return APIResponse(
        data={"reservation": reservation},
        message="Đặt chỗ dung lượng tải lên hoàn tất",
        status=200,
    )
