from typing import Any, Optional
from fastapi import APIRouter, Depends
from src.schemas.user import UserInDB, RoleEnum, UpdateRoleRequest, UpdateStatusRequest, ModerationActionRequest, NoteRequest
from src.api.dependency import get_db, require_role, get_current_user
from core.response import APIResponse
from src.services.user import UserService
from pydantic import BaseModel
router = APIRouter(prefix='/nguoi-dung')

@router.get('', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_all_users(limit: int=50, offset: int=0, db=Depends(get_db)):
    return APIResponse(data=await UserService.get_all_users(limit, offset, db=db), message='Lấy danh sách người dùng thành công')

@router.put('/{user_id}/vai-tro', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def update_user_role(user_id: str, req: UpdateRoleRequest, db=Depends(get_db)):
    return APIResponse(data=await UserService.update_user_role(user_id, req.role, db=db), message='Cập nhật quyền thành công')

@router.put('/{user_id}/trang-thai', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def update_user_status(user_id: str, req: UpdateStatusRequest, db=Depends(get_db)):
    return APIResponse(data=await UserService.update_user_status(user_id, req.is_active, db=db), message='Cập nhật trạng thái tài khoản thành công')

@router.post('/{user_id}/canh-bao', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def warn_user(user_id: str, req: ModerationActionRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await UserService.warn_user(user_id, req.reason, current_user, db=db), message='Gửi cảnh báo thành công')

@router.post('/{user_id}/khoa', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def lock_user(user_id: str, req: ModerationActionRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await UserService.lock_user(user_id, req.reason, req.duration_hours, current_user, db=db), message='Khóa tài khoản thành công')

@router.post('/{user_id}/shadowban', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def shadowban_user(user_id: str, is_banned: bool, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await UserService.shadowban_user(user_id, is_banned, current_user, db=db), message='Cập nhật shadowban thành công')

@router.get('/{user_id}/ghi-chu', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_moderator_notes(user_id: str, db=Depends(get_db)):
    return APIResponse(data=await UserService.get_moderator_notes(user_id, db=db), message='Lấy ghi chú thành công')

@router.post('/{user_id}/ghi-chu', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def add_moderator_note(user_id: str, req: NoteRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await UserService.add_moderator_note(user_id, req.note, current_user, db=db), message='Thêm ghi chú thành công', status=201)

@router.get('/tim-kiem', response_model=APIResponse[Any])
async def search_users(q: str='', limit: int=10, db=Depends(get_db)):
    return APIResponse(data=await UserService.search_users(q, limit, db=db), message='Tìm kiếm người dùng thành công')

@router.get('/noi-bo/{user_id}', response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user(user_id: str, db=Depends(get_db)):
    user = await UserService.internal_get_user_by_id(user_id, db)
    return APIResponse(data=user, message='Lấy thông tin người dùng thành công')

@router.post('/noi-bo/nhieu-nguoi-dung', response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_users(user_ids: list[str], db=Depends(get_db)):
    users = await UserService.internal_get_users_by_ids(user_ids, db)
    return APIResponse(data=users, message='Lấy danh sách người dùng thành công')

@router.get('/noi-bo/email/{email}', response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user_by_email(email: str, db=Depends(get_db)):
    user = await UserService.internal_get_user_by_email(email, db)
    return APIResponse(data=user, message='Lấy thông tin người dùng qua email thành công')

@router.get('/noi-bo/slug/{slug}', response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user_by_slug(slug: str, db=Depends(get_db)):
    user = await UserService.internal_get_user_by_slug(slug, db)
    return APIResponse(data=user, message='Lấy thông tin người dùng qua slug thành công')

class InternalCreateUserRequest(BaseModel):
    email: str
    password_hash: Optional[str] = None
    full_name: str
    role: str = "READER"
    slug: str
    
@router.post('/noi-bo/tao-moi', response_model=APIResponse[Any], include_in_schema=False)
async def internal_create_user(req: InternalCreateUserRequest, db=Depends(get_db)):
    user_id = await UserService.internal_create_user(req.dict(), db)
    return APIResponse(data={"user_id": user_id}, message='Tạo người dùng thành công', status=201)