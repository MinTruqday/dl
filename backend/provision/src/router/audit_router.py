from typing import Any

from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends
from src.router.dependency_router import get_current_user, get_db, require_role
from src.services.user_service import UserService

router = APIRouter(prefix="/audit")


@router.get(
    "/kiem-duyet-vien",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def get_moderator_activity(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await UserService.get_moderator_activity_log(str(current_user.id), db=db),
        message="Đã tải nhật ký hoạt động",
    )
