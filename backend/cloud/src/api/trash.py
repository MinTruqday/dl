from typing import Any
from fastapi import APIRouter, Depends
from src.api.dependency import require_role
from src.core.dependency import CurrentUser, Role
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.services.trash import TrashService

router = APIRouter(route_class=LoggingRoute, prefix="/luu-tru")

@router.delete("/thung-rac/chuyen-vao/{item_id}", response_model=APIResponse[Any])
async def move_to_trash(
    item_id: str,
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await TrashService.move_to_trash(item_id, current_user.id)
    return APIResponse(data=result, message="Đã chuyển tệp/thư mục vào Thùng rác")

@router.post("/thung-rac/khoi-phuc/{item_id}", response_model=APIResponse[Any])
async def restore_from_trash(
    item_id: str,
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await TrashService.restore_from_trash(item_id, current_user.id)
    return APIResponse(data=result, message="Đã khôi phục tệp/thư mục từ Thùng rác")

@router.delete("/thung-rac/don-sach", response_model=APIResponse[Any])
async def empty_trash(
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await TrashService.empty_trash(current_user.id)
    return APIResponse(data=result, message="Đã dọn sạch Thùng rác thành công")
