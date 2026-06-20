from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from src.router.dependency import get_current_user, get_db, require_role
from src.services.user import UserManager

from core.config import settings
from core.response import APIResponse
from core.schemas.user import (ModerationActionRequest, NoteRequest, RoleEnum,
                               UpdateRoleRequest, UpdateStatusRequest,
                               UserInDB)

router = APIRouter(prefix="/users")


@router.get(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_all_users(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    offset: int = 0,
    db=Depends(get_db),
):
    return APIResponse(
        data=await UserManager.get_all_users(limit, offset, db=db),
        message="Lấy danh sách người dùng thành công",
    )


@router.put(
    "/{user_id}/role",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def update_user_role(user_id: str, req: UpdateRoleRequest, db=Depends(get_db)):
    return APIResponse(
        data=await UserManager.update_user_role(user_id, req.role, db=db),
        message="Cập nhật quyền truy cập tài khoản thành công",
    )


@router.put(
    "/{user_id}/status",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def update_user_status(
    user_id: str, req: UpdateStatusRequest, db=Depends(get_db)
):
    return APIResponse(
        data=await UserManager.update_user_status(user_id, req.is_active, db=db),
        message="Cập nhật trạng thái hoạt động thành công",
    )


@router.post(
    "/{user_id}/warn",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def warn_user(
    user_id: str,
    req: ModerationActionRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await UserManager.warn_user(user_id, req.reason, current_user, db=db),
        message="Gửi cảnh báo vi phạm thành công",
    )


@router.post(
    "/{user_id}/lock",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def lock_user(
    user_id: str,
    req: ModerationActionRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await UserManager.lock_user(
            user_id, req.reason, req.duration_hours, current_user, db=db
        ),
        message="Khóa tài khoản tạm thời thành công",
    )


@router.post(
    "/{user_id}/shadowban",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def shadowban_user(
    user_id: str,
    is_banned: bool,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await UserManager.shadowban_user(user_id, is_banned, current_user, db=db),
        message="Cập nhật quyền hiển thị tài khoản thành công",
    )


@router.get(
    "/{user_id}/notes",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_notes(user_id: str, db=Depends(get_db)):
    return APIResponse(
        data=await UserManager.get_notes(user_id, db=db),
        message="Lấy ghi chú kiểm duyệt thành công",
    )


@router.post(
    "/{user_id}/notes",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def add_note(
    user_id: str,
    req: NoteRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await UserManager.add_note(user_id, req.note, current_user, db=db),
        message="Lưu ghi chú kiểm duyệt vào hồ sơ thành công",
        status=201,
    )


@router.get("/search", response_model=APIResponse[Any])
async def search_users(
    q: str = "",
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    db=Depends(get_db),
):
    return APIResponse(
        data=await UserManager.search_users(q, limit, db=db),
        message="Lấy kết quả tìm kiếm thành công",
    )


@router.get("/{user_id}", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user(user_id: str, db=Depends(get_db)):
    user = await UserManager.internal_get_user_by_id(user_id, db)
    return APIResponse(
        data=user, message="Lấy thông tin chi tiết hồ sơ người dùng thành công"
    )


@router.post(
    "/multiple-users", response_model=APIResponse[Any], include_in_schema=False
)
async def internal_get_users(user_ids: list[str], db=Depends(get_db)):
    users = await UserManager.internal_get_users_by_ids(user_ids, db)
    return APIResponse(data=users, message="Lấy danh sách người dùng thành công")


@router.get("/email/{email}", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user_by_email(email: str, db=Depends(get_db)):
    user = await UserManager.internal_get_user_by_email(email, db)
    return APIResponse(
        data=user, message="Lấy thông tin chi tiết hồ sơ người dùng thành công"
    )


@router.get("/slug/{slug}", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user_by_slug(slug: str, db=Depends(get_db)):
    user = await UserManager.internal_get_user_by_slug(slug, db)
    return APIResponse(
        data=user, message="Lấy thông tin chi tiết hồ sơ người dùng thành công"
    )


class InternalCreateUserRequest(BaseModel):
    email: str
    password_hash: Optional[str] = None
    full_name: str
    role: str = "READER"
    slug: str


@router.post("/", response_model=APIResponse[Any], include_in_schema=False)
async def internal_create_user(req: InternalCreateUserRequest, db=Depends(get_db)):
    user_id = await UserManager.internal_create_user(req.dict(), db)
    return APIResponse(
        data={"user_id": user_id},
        message="Tạo tài khoản người dùng thành công",
        status=201,
    )
