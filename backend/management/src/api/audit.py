from src.core.dependency import CurrentUser
from typing import Any

from fastapi import APIRouter, Depends
from src.services.account import AccountService

from src.core.dependency import get_current_user, get_db, require_role
from src.core.response import APIResponse
from src.schemas.account import Role, UserInDB

router = APIRouter(prefix="/kiem-toan")


@router.get(
    "/logs",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.ADMIN]))],
)
async def get_activity(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await AccountService.get_moderator_activity_log(str(current_user.id), db=db),
        message="Lấy nhật ký hoạt động thành công",
    )
