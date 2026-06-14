from typing import Any
from fastapi import APIRouter, Depends
from core.dependency import get_db, require_role, get_current_user
from core.schemas.user import UserInDB, RoleEnum
from core.response import APIResponse
from src.services.user_service import UserService

router = APIRouter(prefix="/audit")


@router.get(
    "/logs",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def get_moderator_activity(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await UserService.get_moderator_activity_log(str(current_user.id), db=db),
        message="Activity logs retrieved successfully",
    )
