from typing import Any, Optional

from core.response import APIResponse
from core.schemas.user import (ModerationActionRequest, NoteRequest, RoleEnum,
                               UpdateRoleRequest, UpdateStatusRequest,
                               UserInDB)
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api.dependency import get_current_user, get_db, require_role
from src.services.user import UserService

router = APIRouter(prefix="/user")


@router.get(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))],
)
async def get_all_users(limit: int = 50, offset: int = 0, db=Depends(get_db)):
    return APIResponse(
        data=await UserService.get_all_users(limit, offset, db=db),
        message="Đã tải danh sách người dùng",
    )


@router.put(
    "/{user_id}/vai-tro",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def update_user_role(user_id: str, req: UpdateRoleRequest, db=Depends(get_db)):
    return APIResponse(
        data=await UserService.update_user_role(user_id, req.role, db=db),
        message="Đã cập nhật quyền truy cập",
    )


@router.put(
    "/{user_id}/status",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))],
)
async def update_user_status(
    user_id: str, req: UpdateStatusRequest, db=Depends(get_db)
):
    return APIResponse(
        data=await UserService.update_user_status(user_id, req.is_active, db=db),
        message="Đã cập nhật trạng thái hoạt động",
    )


@router.post(
    "/{user_id}/canh-bao",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def warn_user(
    user_id: str,
    req: ModerationActionRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await UserService.warn_user(user_id, req.reason, current_user, db=db),
        message="Đã gửi cảnh báo",
    )


@router.post(
    "/{user_id}/khoa",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def lock_user(
    user_id: str,
    req: ModerationActionRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await UserService.lock_user(
            user_id, req.reason, req.duration_hours, current_user, db=db
        ),
        message="Đã khóa tài khoản",
    )


@router.post(
    "/{user_id}/shadowban",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def shadowban_user(
    user_id: str,
    is_banned: bool,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await UserService.shadowban_user(user_id, is_banned, current_user, db=db),
        message="Đã áp dụng trạng thái hạn chế",
    )


@router.get(
    "/{user_id}/ghi-chu",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def get_moderator_notes(user_id: str, db=Depends(get_db)):
    return APIResponse(
        data=await UserService.get_moderator_notes(user_id, db=db),
        message="Đã tải ghi chú điều hành",
    )


@router.post(
    "/{user_id}/ghi-chu",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def add_moderator_note(
    user_id: str,
    req: NoteRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await UserService.add_moderator_note(
            user_id, req.note, current_user, db=db
        ),
        message="Đã thêm ghi chú",
        status=201,
    )


@router.get("/tim-kiem", response_model=APIResponse[Any])
async def search_users(q: str = "", limit: int = 10, db=Depends(get_db)):
    return APIResponse(
        data=await UserService.search_users(q, limit, db=db),
        message="Đã hoàn tất tìm kiếm người dùng",
    )


@router.get("/{user_id}", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user(user_id: str, db=Depends(get_db)):
    user = await UserService.internal_get_user_by_id(user_id, db)
    return APIResponse(data=user, message="Đã tải thông tin người dùng")


@router.post(
    "/multiple-users", response_model=APIResponse[Any], include_in_schema=False
)
async def internal_get_users(user_ids: list[str], db=Depends(get_db)):
    users = await UserService.internal_get_users_by_ids(user_ids, db)
    return APIResponse(data=users, message="Đã tải danh sách người dùng")


@router.get("/email/{email}", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user_by_email(email: str, db=Depends(get_db)):
    user = await UserService.internal_get_user_by_email(email, db)
    return APIResponse(data=user, message="Đã tải thông tin người dùng")


@router.get("/slug/{slug}", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user_by_slug(slug: str, db=Depends(get_db)):
    user = await UserService.internal_get_user_by_slug(slug, db)
    return APIResponse(data=user, message="Đã tải thông tin người dùng")


class InternalCreateUserRequest(BaseModel):
    email: str
    password_hash: Optional[str] = None
    full_name: str
    role: str = "READER"
    slug: str


@router.post("/create", response_model=APIResponse[Any], include_in_schema=False)
async def internal_create_user(req: InternalCreateUserRequest, db=Depends(get_db)):
    user_id = await UserService.internal_create_user(req.dict(), db)
    return APIResponse(
        data={"user_id": user_id}, message="Đã tạo tài khoản", status=201
    )
