from typing import Any, List, Optional
from fastapi import APIRouter, Body, Depends, Query
from src.api.dependency import require_role
from src.core.dependency import CurrentUser, Role
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.services.search import SearchService

router = APIRouter(route_class=LoggingRoute, prefix="/luu-tru")

@router.post(
    "/nhan-ban/{item_id}",
    response_model=APIResponse[Any],
    status_code=201,
)
async def duplicate_item(
    item_id: str,
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await SearchService.duplicate_item(item_id, current_user.id)
    return APIResponse(data=result, message="Nhân bản tệp thành công", status=201)

@router.get("/tim-kiem-nang-cao", response_model=APIResponse[Any])
async def advanced_search(
    q: Optional[str] = Query(None),
    mime_type: Optional[str] = Query(None),
    extension: Optional[str] = Query(None),
    min_size_mb: Optional[float] = Query(None),
    max_size_mb: Optional[float] = Query(None),
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await SearchService.advanced_search(current_user.id, q, mime_type, extension, min_size_mb, max_size_mb)
    return APIResponse(data=result, message="Tìm kiếm tệp nâng cao hoàn tất")

@router.post("/thu-muc/{folder_id}/mau-sac", response_model=APIResponse[Any])
async def set_folder_color(
    folder_id: str,
    color_hex: str = Body(..., embed=True),
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await SearchService.set_folder_color(folder_id, current_user.id, color_hex)
    return APIResponse(data=result, message="Cập nhật màu sắc thư mục hoàn tất")

@router.post("/phieu-tag/{item_id}", response_model=APIResponse[Any])
async def update_item_tags(
    item_id: str,
    tags: List[str] = Body(..., embed=True),
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await SearchService.update_item_tags(item_id, current_user.id, tags)
    return APIResponse(data=result, message="Cập nhật thẻ nhãn tài liệu hoàn tất")

@router.get("/xem-truoc/{item_id}", response_model=APIResponse[Any])
async def get_preview_payload(
    item_id: str,
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN, Role.READER])),
):
    result = await SearchService.get_preview_payload(item_id, current_user.id)
    return APIResponse(data=result, message="Trích xuất dữ liệu xem trước tệp hoàn tất")
