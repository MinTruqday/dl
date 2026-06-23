from shared.dependencies import CurrentUser
from typing import Any

from fastapi import APIRouter, Depends
from src.services.profiles import UserIdentity

from shared.dependencies import get_current_user, get_db, require_role
from shared.responses import APIResponse
from src.schemas.profiles import RoleEnum, UserInDB

router = APIRouter(prefix="/kiem-toan")


@router.get(
    "/logs",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_activity(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await UserIdentity.get_moderator_activity_log(str(current_user.id), db=db),
        message="Lấy nhật ký hoạt động thành công",
    )
