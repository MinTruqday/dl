from typing import Any
from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from fastapi import APIRouter, Depends
from src.services.users import UserService

router = APIRouter(prefix="/kiem-toan")

@router.get("/nhat-ky", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_activity(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await UserService.get_activity_log(str(current_user.get("id")), db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )