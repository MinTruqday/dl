from core.system_dependency import CurrentUser
from typing import Any

from fastapi import APIRouter, Depends
from src.services.user_profile import UserIdentity

from core.system_dependency import get_current_user, get_db, require_role
from core.api_response import APIResponse
from src.schemas.user_identity import RoleEnum, UserInDB

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
        data=await UserIdentity.get_activity_log(str(current_user.id), db=db),
        message="Lấy nhật ký hoạt động thành công",
    )
