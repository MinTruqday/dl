from typing import Any, Optional
from fastapi import APIRouter, Depends
from shared.models.user import UserInDB, RoleEnum
from api.dependency import require_role, get_current_user
from shared.core.response import APIResponse
from services.user import UserService
from pydantic import BaseModel
router = APIRouter(prefix="/nguoi-dung")
class UpdateRoleRequest(BaseModel):
    role: str
class UpdateStatusRequest(BaseModel):
    is_active: bool
class ModerationActionRequest(BaseModel):
    reason: str
    duration_hours: Optional[int] = 24
class NoteRequest(BaseModel):
    note: str
@router.get("", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_all_users(limit: int = 50, offset: int = 0):
    return APIResponse(
        data=await UserService.get_all_users(limit, offset), 
        message="Lấy danh sách người dùng thành công"
    )
@router.put("/{user_id}/vai-tro", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def update_user_role(user_id: str, req: UpdateRoleRequest):
    return APIResponse(
        data=await UserService.update_user_role(user_id, req.role), 
        message="Cập nhật quyền thành công"
    )
@router.put("/{user_id}/trang-thai", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def update_user_status(user_id: str, req: UpdateStatusRequest):
    return APIResponse(
        data=await UserService.update_user_status(user_id, req.is_active), 
        message="Cập nhật trạng thái tài khoản thành công"
    )
@router.post("/{user_id}/canh-bao", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def warn_user(user_id: str, req: ModerationActionRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await UserService.warn_user(user_id, req.reason, current_user),
        message="Gửi cảnh báo thành công"
    )
@router.post("/{user_id}/khoa", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def lock_user(user_id: str, req: ModerationActionRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await UserService.lock_user(user_id, req.reason, req.duration_hours, current_user),
        message="Khóa tài khoản thành công"
    )
@router.post("/{user_id}/shadowban", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def shadowban_user(user_id: str, is_banned: bool, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await UserService.shadowban_user(user_id, is_banned, current_user),
        message="Cập nhật shadowban thành công"
    )
@router.get("/{user_id}/ghi-chu", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_moderator_notes(user_id: str):
    return APIResponse(
        data=await UserService.get_moderator_notes(user_id),
        message="Lấy ghi chú thành công"
    )
@router.post("/{user_id}/ghi-chu", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def add_moderator_note(user_id: str, req: NoteRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await UserService.add_moderator_note(user_id, req.note, current_user),
        message="Thêm ghi chú thành công",
        status=201
    )
