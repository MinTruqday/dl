from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from src.api.dependency import require_role
from src.core.dependency import CurrentUser, Role
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.services.share import ShareService
from src.schemas.storage import ProtectedShareCreate

router = APIRouter(route_class=LoggingRoute, prefix="/luu-tru")

@router.post(
    "/link-chia-se/tao",
    response_model=APIResponse[Any],
    status_code=201,
)
async def create_protected_share_link(
    req: ProtectedShareCreate,
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await ShareService.create_protected_share_link(
        req.item_id,
        current_user.id,
        req.password,
        req.expires_in_hours,
    )
    return APIResponse(data=result, message="Tạo link chia sẻ bảo mật hoàn tất", status=201)

@router.get("/link-chia-se/xac-thuc/{token}", response_model=APIResponse[Any])
async def validate_protected_share_link(
    token: str,
    password: Optional[str] = Query(default=None, max_length=128),
):
    result = await ShareService.validate_protected_share_link(token, password)
    return APIResponse(data=result, message="Xác thực truy cập đường dẫn chia sẻ thành công")
