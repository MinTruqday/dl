from typing import Any

from fastapi import APIRouter, Depends
from src.services.user import UserService

from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB

router = APIRouter(prefix="/audit")


@router.get(
    "/logs",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_activity(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await UserService.get_activity_log(str(current_user.id), db=db),
        message="Lấy nhật ký hoạt động thành công",
    )
