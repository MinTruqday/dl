from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from src.router.dependency import get_current_user, get_db, require_role
from src.services.quota import QuotaManager

from core.response import APIResponse
from core.schemas.quota import QuotaLimit
from core.schemas.user import RoleEnum, UserInDB

router = APIRouter(prefix="/han-muc")


@router.get("/kiem-tra", response_model=APIResponse[Any], include_in_schema=False)
async def check_quota_internal(
    user_id: str,
    role: str,
    ai_tier: str = "BASIC",
    feature: str = "chat",
    db=Depends(get_db),
):
    limits = await QuotaManager.check_quota(user_id, role, ai_tier, feature, db=db)
    return APIResponse(
        data=limits.model_dump(),
        message="Thao tác nằm trong giới hạn sử dụng cho phép",
        status=200,
    )


@router.get("/ca-nhan", response_model=APIResponse[Any])
async def get_my_quota(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    usage = await QuotaManager.get_current_usage(
        str(current_user.id), current_user.role.value, current_user.ai_tier.value, db=db
    )
    return APIResponse(data=usage, message="Lấy thông tin hạn mức sử dụng thành công")


@router.put("/{role}/cau-hinh", response_model=APIResponse[Any])
async def update_role_quota(
    role: str,
    limits: QuotaLimit,
    current_user: UserInDB = Depends(require_role([RoleEnum.ADMIN])),
    db=Depends(get_db),
):
    await QuotaManager.update_role_quota(role, limits.model_dump(), db=db)
    return APIResponse(
        data={},
        message="Cập nhật giới hạn tài nguyên thành công",
    )


@router.get("/cau-hinh", response_model=APIResponse[Any])
async def get_global_config(
    current_user: UserInDB = Depends(require_role([RoleEnum.ADMIN])), db=Depends(get_db)
):
    global_cfg = await QuotaManager.get_global_config_from_db(db=db)
    return APIResponse(
        data=global_cfg,
        message="Lấy cấu hình tài nguyên thành công",
    )


from pydantic import BaseModel


class ConsumeQuotaRequest(BaseModel):
    user_id: str
    feature: str = "chat"
    req_reset_hours: int = 24
    tokens: int = 0


@router.post("/tieu-thu", response_model=APIResponse[Any], include_in_schema=False)
async def consume_quota(req: ConsumeQuotaRequest, db=Depends(get_db)):
    await QuotaManager.consume_request(
        req.user_id, req.feature, req.req_reset_hours, db=db
    )
    if req.tokens > 0:
        await QuotaManager.consume_tokens(
            req.user_id, req.tokens, req.feature, req.req_reset_hours, db=db
        )
    return APIResponse(
        data=None, message="Sử dụng dung lượng tài nguyên thành công", status=200
    )
