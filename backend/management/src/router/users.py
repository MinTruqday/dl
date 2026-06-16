from typing import Any
from core.config import settings
from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from src.schemas.management import InternalCreateUserRequest
from src.schemas.users import (
    UpdateRoleRequest,
    UpdateStatusRequest,
    ModerationActionRequest,
    NoteRequest,
)
from src.services.users import UserService

router = APIRouter(prefix="/nguoi-dung")

@router.get("", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_all_users(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), offset: int = 0, db=Depends(get_db)):
    return APIResponse(
        data=await UserService.get_all_users(limit, offset, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.put("/{user_id}/vai-tro", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def update_user_role(user_id: str, req: UpdateRoleRequest, db=Depends(get_db)):
    return APIResponse(
        data=await UserService.update_user_role(user_id, req.role, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.put("/{user_id}/trang-thai", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def update_user_status(user_id: str, req: UpdateStatusRequest, db=Depends(get_db)):
    return APIResponse(
        data=await UserService.update_user_status(user_id, req.is_active, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.post("/{user_id}/canh-bao", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def warn_user(user_id: str, req: ModerationActionRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await UserService.warn_user(user_id, req.reason, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.post("/{user_id}/khoa-lai", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def lock_user(user_id: str, req: ModerationActionRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await UserService.lock_user(user_id, req.reason, req.duration_hours, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.post("/{user_id}/cam-quyen-ngam", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def shadowban_user(user_id: str, is_banned: bool, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await UserService.shadowban_user(user_id, is_banned, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.get("/{user_id}/ghi-chu", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_notes(user_id: str, db=Depends(get_db)):
    return APIResponse(
        data=await UserService.get_notes(user_id, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.post("/{user_id}/ghi-chu", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def add_note(user_id: str, req: NoteRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await UserService.add_note(user_id, req.note, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=201,
    )

@router.get("/tim-kiem", response_model=APIResponse[Any])
async def search_users(q: str = "", limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), db=Depends(get_db)):
    return APIResponse(
        data=await UserService.search_users(q, limit, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.get("/{user_id}", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user(user_id: str, db=Depends(get_db)):
    user = await UserService.internal_get_user_by_id(user_id, db)
    return APIResponse(data=user, message="Khởi tạo AI thành công")

@router.post("/hang-loat", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_users(user_ids: list[str], db=Depends(get_db)):
    users = await UserService.internal_get_users_by_ids(user_ids, db)
    return APIResponse(data=users, message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")

@router.get("/thu-dien/{email}", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user_by_email(email: str, db=Depends(get_db)):
    user = await UserService.internal_get_user_by_email(email, db)
    return APIResponse(data=user, message="Khởi tạo AI thành công")

@router.get("/dinh-danh/{slug}", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user_by_slug(slug: str, db=Depends(get_db)):
    user = await UserService.internal_get_user_by_slug(slug, db)
    return APIResponse(data=user, message="Khởi tạo AI thành công")

@router.post("", response_model=APIResponse[Any], status_code=201, include_in_schema=False)
async def internal_create_user(req: InternalCreateUserRequest, db=Depends(get_db)):
    user_id = await UserService.internal_create_user(req.model_dump(), db)
    return APIResponse(
        data={"user_id": user_id},
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=201
    )