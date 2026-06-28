from src.core.dependency import CurrentUser
from typing import Any, Optional

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Query
from src.api.dependency import get_current_user, get_db, require_role
from src.services.account import AccountService

from src.core.infrastructure.configuration import settings
from src.core.response import APIResponse
from src.schemas.account import (
    ModerationActionRequest,
    NoteRequest,
    Role,
    UpdateRoleRequest,
    UpdateStatusRequest,
    UserInDB,
    InternalCreateUserRequest,
)

router = APIRouter(route_class=LoggingRoute, prefix="/nguoi-dung")

@router.get(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_all_users(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    offset: int = 0,
    db=Depends(get_db),
):
    return APIResponse(
        data=await AccountService.get_all_users(limit, offset),
        message="Lấy danh sách người dùng thành công",
    )

@router.put(
    "/{user_id}/vai-tro",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def update_user_role(user_id: str, req: UpdateRoleRequest, db=Depends(get_db)):
    return APIResponse(
        data=await AccountService.update_user_role(user_id, req.role),
        message="Cập nhật quyền truy cập tài khoản thành công",
    )

@router.put(
    "/{user_id}/trang-thai",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def update_user_status(
    user_id: str, req: UpdateStatusRequest, db=Depends(get_db)
):
    return APIResponse(
        data=await AccountService.update_user_status(user_id, req.is_active),
        message="Cập nhật trạng thái hoạt động thành công",
    )

@router.post(
    "/{user_id}/canh-bao",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def warn_user(
    user_id: str,
    req: ModerationActionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AccountService.warn_user(user_id, req.reason, current_user),
        message="Gửi cảnh báo vi phạm thành công",
    )

@router.post(
    "/{user_id}/khoa",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def lock_user(
    user_id: str,
    req: ModerationActionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AccountService.lock_user(
            user_id, req.reason, req.duration_hours, current_user
        ),
        message="Khóa tài khoản tạm thời thành công",
    )

@router.post(
    "/{user_id}/cam-ngam",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def shadowban_user(
    user_id: str,
    is_banned: bool,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AccountService.shadowban_user(user_id, is_banned, current_user),
        message="Cập nhật quyền hiển thị tài khoản thành công",
    )

@router.get(
    "/{user_id}/ghi-chu",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_notes(user_id: str, db=Depends(get_db)):
    return APIResponse(
        data=await AccountService.get_notes(user_id),
        message="Lấy ghi chú kiểm duyệt thành công",
    )

@router.post(
    "/{user_id}/ghi-chu",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def add_note(
    user_id: str,
    req: NoteRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AccountService.add_note(user_id, req.note, current_user),
        message="Lưu ghi chú kiểm duyệt vào hồ sơ thành công",
        status=201,
    )

@router.get("/tim-kiem", response_model=APIResponse[Any])
async def search_users(
    q: str = "",
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    db=Depends(get_db),
):
    return APIResponse(
        data=await AccountService.search_users(q, limit),
        message="Lấy kết quả tìm kiếm thành công",
    )

@router.get("/{user_id}", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user(user_id: str, db=Depends(get_db)):
    user = await AccountService.internal_get_user_by_id(user_id, db)
    return APIResponse(
        data=user, message="Lấy thông tin chi tiết hồ sơ người dùng thành công"
    )

@router.post("/danh-sach", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_users(user_ids: list[str], db=Depends(get_db)):
    users = await AccountService.internal_get_users_by_ids(user_ids, db)
    return APIResponse(data=users, message="Lấy danh sách người dùng thành công")

@router.get("/email/{email}", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user_by_email(email: str, db=Depends(get_db)):
    user = await AccountService.internal_get_user_by_email(email, db)
    return APIResponse(
        data=user, message="Lấy thông tin chi tiết hồ sơ người dùng thành công"
    )

@router.get(
    "/ten-mien/{slug}", response_model=APIResponse[Any], include_in_schema=False
)
async def internal_get_user_by_slug(slug: str, db=Depends(get_db)):
    user = await AccountService.internal_get_user_by_slug(slug, db)
    return APIResponse(
        data=user, message="Lấy thông tin chi tiết hồ sơ người dùng thành công"
    )

@router.post("/", response_model=APIResponse[Any], include_in_schema=False)
async def internal_create_user(req: InternalCreateUserRequest, db=Depends(get_db)):
    user_id = await AccountService.internal_create_user(req.dict(), db)
    return APIResponse(
        data={"user_id": user_id},
        message="Tạo tài khoản người dùng thành công",
        status=201,
    )
