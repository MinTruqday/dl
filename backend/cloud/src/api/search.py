from typing import Any, List
from fastapi import APIRouter, Body, Depends
from src.api.dependency import require_role
from src.core.dependency import CurrentUser, Role
from src.core.response import APIResponse
from src.services.search import SearchService

router = APIRouter(prefix="/luu-tru")


@router.post("/nhan-ban/{item_id}", response_model=APIResponse[Any], status_code=201)
async def duplicate_item(
    item_id: str,
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await SearchService.duplicate_item(item_id, current_user.id)
    return APIResponse(data=result, message="Nhân bản tệp thành công", status=201)


@router.post("/thu-muc/{folder_id}/mau-sac", response_model=APIResponse[Any])
async def set_folder_color(
    folder_id: str,
    color_hex: str = Body(..., embed=True),
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await SearchService.set_folder_color(folder_id, current_user.id, color_hex)
    return APIResponse(data=result, message="Cập nhật màu sắc thư mục hoàn tất")


@router.post("/phieu-nhan/{item_id}", response_model=APIResponse[Any])
async def update_item_tags(
    item_id: str,
    tags: List[str] = Body(..., embed=True),
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await SearchService.update_item_tags(item_id, current_user.id, tags)
    return APIResponse(data=result, message="Cập nhật thẻ nhãn tài liệu hoàn tất")
