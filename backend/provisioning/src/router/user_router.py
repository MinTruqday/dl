from typing import Any, Optional

from core.response import APIResponse
from core.schemas.user import (
    ModerationActionRequest,
    NoteRequest,
    RoleEnum,
    UpdateRoleRequest,
    UpdateStatusRequest,
    UserInDB,
)
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from src.router.dependency_router import get_current_user, get_db, require_role
from src.services.user_service import UserService
from core.config import settings

router = APIRouter(prefix="/users")


@router.get(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR]))],
)
async def get_all_users(
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    offset: int = 0,
    db=Depends(get_db),
):
    return APIResponse(
        data=await UserService.get_all_users(limit, offset, db=db),
        message="The requested list of user accounts has been successfully retrieved from the system",
    )


@router.put(
    "/{user_id}/role",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def update_user_role(user_id: str, req: UpdateRoleRequest, db=Depends(get_db)):
    return APIResponse(
        data=await UserService.update_user_role(user_id, req.role, db=db),
        message="The access privileges for the specified user account have been successfully modified",
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
        message="The operational activity status for the specified user account has been updated successfully",
    )


@router.post(
    "/{user_id}/warn",
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
        message="The official administrative warning has been successfully dispatched to the targeted user",
    )


@router.post(
    "/{user_id}/lock",
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
        message="The specified user account has been successfully locked and temporarily restricted",
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
        message="The visibility restriction protocol has been successfully updated for the specified account",
    )


@router.get(
    "/{user_id}/notes",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def get_moderator_notes(user_id: str, db=Depends(get_db)):
    return APIResponse(
        data=await UserService.get_moderator_notes(user_id, db=db),
        message="The internal administrative moderation notes have been successfully retrieved",
    )


@router.post(
    "/{user_id}/notes",
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
        message="The internal administrative moderation note has been successfully saved to the user profile",
        status=201,
    )


@router.get("/search", response_model=APIResponse[Any])
async def search_users(
    q: str = "",
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    db=Depends(get_db),
):
    return APIResponse(
        data=await UserService.search_users(q, limit, db=db),
        message="The user search query has been successfully executed and the matching results are returned",
    )


@router.get("/{user_id}", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user(user_id: str, db=Depends(get_db)):
    user = await UserService.internal_get_user_by_id(user_id, db)
    return APIResponse(data=user, message="The detailed profile information for the specified user has been successfully retrieved")


@router.post(
    "/multiple-users", response_model=APIResponse[Any], include_in_schema=False
)
async def internal_get_users(user_ids: list[str], db=Depends(get_db)):
    users = await UserService.internal_get_users_by_ids(user_ids, db)
    return APIResponse(data=users, message="The requested list of user accounts matching the provided identifiers has been successfully retrieved")


@router.get("/email/{email}", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user_by_email(email: str, db=Depends(get_db)):
    user = await UserService.internal_get_user_by_email(email, db)
    return APIResponse(data=user, message="The detailed profile information for the specified user has been successfully retrieved")


@router.get("/slug/{slug}", response_model=APIResponse[Any], include_in_schema=False)
async def internal_get_user_by_slug(slug: str, db=Depends(get_db)):
    user = await UserService.internal_get_user_by_slug(slug, db)
    return APIResponse(data=user, message="The detailed profile information for the specified user has been successfully retrieved")


class InternalCreateUserRequest(BaseModel):
    email: str
    password_hash: Optional[str] = None
    full_name: str
    role: str = "READER"
    slug: str


@router.post("/", response_model=APIResponse[Any], include_in_schema=False)
async def internal_create_user(req: InternalCreateUserRequest, db=Depends(get_db)):
    user_id = await UserService.internal_create_user(req.dict(), db)
    return APIResponse(
        data={"user_id": user_id}, message="The new user account has been successfully provisioned and registered in the system", status=201
    )