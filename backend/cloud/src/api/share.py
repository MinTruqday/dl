from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from src.core.dependency import CurrentUser, get_current_user
from src.core.response import APIResponse
from src.schemas.storage import ProtectedShareCreate
from src.services.share import ShareService

router = APIRouter(prefix="/luu-tru")


@router.post("/lien-ket-chia-se/tao", response_model=APIResponse[Any], status_code=201)
async def create_protected_share_link(
    req: ProtectedShareCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await ShareService.create_protected_share_link(
        req.item_id, current_user.id, req.password, req.expires_in_hours
    )
    return APIResponse(data=result, message="Tạo link chia sẻ bảo mật hoàn tất", status=201)


@router.get("/lien-ket-chia-se/xac-thuc/{token}", response_model=APIResponse[Any])
async def validate_protected_share_link(
    token: str, password: Optional[str] = Query(default=None, max_length=128)
):
    result = await ShareService.validate_protected_share_link(token, password)
    return APIResponse(data=result, message="Xác thực truy cập đường dẫn chia sẻ thành công")
