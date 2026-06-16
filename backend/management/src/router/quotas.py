from typing import Any
from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from fastapi import APIRouter, Depends
from src.schemas.management import ConsumeQuotaRequest
from src.schemas.quotas import QuotaLimit
from src.services.quotas import QuotaService

router = APIRouter(prefix="/han-muc")

@router.get("/kiem-tra", response_model=APIResponse[Any], include_in_schema=False)
async def check_quota_internal(user_id: str, role: str, ai_tier: str = "BASIC", feature: str = "chat", db=Depends(get_db)):
    limits = await QuotaService.check_quota(user_id, role, ai_tier, feature, db=db)
    return APIResponse(
        data=limits.model_dump(),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
        status=200
    )

@router.get("/me", response_model=APIResponse[Any])
async def get_my_quota(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    usage = await QuotaService.get_current_usage(str(current_user.get("id")), current_user.get("role").value, current_user.ai_tier.value, db=db)
    return APIResponse(
        data=usage,
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.put("/{role}/cau-hinh", response_model=APIResponse[Any])
async def update_role_quota(role: str, limits: QuotaLimit, current_user: dict = Depends(require_role(["admin"])), db=Depends(get_db)):
    await QuotaService.update_role_quota(role, limits.model_dump(), db=db)
    return APIResponse(
        data={},
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.get("/cau-hinh", response_model=APIResponse[Any])
async def get_global_config(current_user: dict = Depends(require_role(["admin"])), db=Depends(get_db)):
    global_cfg = await QuotaService.get_global_config_from_db(db=db)
    return APIResponse(
        data=global_cfg,
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
    )

@router.post("/tieu-thu", response_model=APIResponse[Any], include_in_schema=False)
async def consume_quota(req: ConsumeQuotaRequest, db=Depends(get_db)):
    await QuotaService.consume_request(req.user_id, req.feature, req.req_reset_hours, db=db)
    if req.tokens > 0:
        await QuotaService.consume_tokens(req.user_id, req.tokens, req.feature, req.req_reset_hours, db=db)
    return APIResponse(
        data=None,
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200
    )