from typing import Any
from fastapi import APIRouter, Depends
from api.dependency import require_role, get_current_user
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.user import UserService

router = APIRouter(prefix="/nhat-ky")

@router.get("/kiem-duyet-vien", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_moderator_activity(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await UserService.get_moderator_activity_log(str(current_user.id)),
        message="Lấy nhật ký hoạt động thành công"
    )
