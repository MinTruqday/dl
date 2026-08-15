from typing import Any
from fastapi import APIRouter, Depends
from src.api.dependency import require_role
from src.core.dependency import CurrentUser, Role
from src.core.response import APIResponse
from src.services.star import StarService

router = APIRouter(prefix="/luu-tru")

@router.post("/danh-dau-sao/{item_id}", response_model=APIResponse[Any])
async def toggle_star_item(
    item_id: str,
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await StarService.toggle_star_item(item_id, current_user.id)
    return APIResponse(data=result, message="Cập nhật trạng thái gắn sao hoàn tất")

@router.get("/danh-dau-sao/danh-sach", response_model=APIResponse[Any])
async def get_starred_items(
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await StarService.get_starred_items(current_user.id)
    return APIResponse(data=result, message="Trích xuất danh sách tệp nổi bật hoàn tất")
