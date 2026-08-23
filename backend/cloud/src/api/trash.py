from typing import Any
from fastapi import APIRouter, Depends
from src.core.response import APIResponse
from src.api.dependency import get_db, require_role
from src.core.dependency import CurrentUser, Role
from src.services.trash import TrashService

router = APIRouter(prefix="/thung-rac")


@router.post("/{item_id}/chuyen-vao", response_model=APIResponse[Any])
async def move_to_trash(
    item_id: str,
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    res = await TrashService.move_to_trash(item_id, current_user.id)
    return APIResponse(data=res, message="Đã chuyển vào thùng rác")


@router.post("/{item_id}/khoi-phuc", response_model=APIResponse[Any])
async def restore_from_trash(
    item_id: str,
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    res = await TrashService.restore_from_trash(item_id, current_user.id)
    return APIResponse(data=res, message="Đã khôi phục từ thùng rác")


@router.delete("/don-sach", response_model=APIResponse[Any])
async def empty_trash(
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    res = await TrashService.empty_trash(current_user.id)
    return APIResponse(data=res, message="Đã dọn sạch thùng rác")


@router.delete("/tu-dong-don", response_model=APIResponse[Any])
async def auto_purge_trash(
    days: int = 30,
    current_user: CurrentUser = Depends(require_role([Role.READER, Role.AUTHOR, Role.ADMIN])),
    db=Depends(get_db),
):
    res = await TrashService.auto_purge_expired_trash(current_user.id, days=days)
    return APIResponse(data=res, message=f"Đã tự động dọn các mục quá hạn {days} ngày")
