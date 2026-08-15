from typing import Any
from fastapi import APIRouter, Depends
from src.api.dependency import get_db, require_role
from src.services.lock import LockService
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(prefix="/cong-tac")

MEMBER_ROLES = [Role.AUTHOR, Role.READER, Role.ADMIN]

@router.post("/tai-lieu/{document_id}/khoa", response_model=APIResponse[Any])
async def acquire_lock(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await LockService.acquire_lock(document_id, current_user),
        message="Thiết lập khóa phiên chỉnh sửa tài liệu hoàn tất",
    )

@router.post("/tai-lieu/{document_id}/mo-khoa", response_model=APIResponse[Any])
async def release_lock(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await LockService.release_lock(document_id, current_user),
        message="Hủy khóa phiên chỉnh sửa tài liệu hoàn tất",
    )

@router.get("/tai-lieu/{document_id}/trang-thai-khoa", response_model=APIResponse[Any])
async def get_lock_status(
    document_id: str,
    current_user: CurrentUser = Depends(require_role(MEMBER_ROLES)),
    db=Depends(get_db),
):
    return APIResponse(
        data=await LockService.get_lock_status(document_id),
        message="Kiểm tra trạng thái khóa phiên chỉnh sửa hiện tại hoàn tất",
    )
