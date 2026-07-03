from fastapi import APIRouter, Depends
from typing import Any
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.core.dependency import get_current_user, get_db, CurrentUser
from src.services.user import UserService
from src.schemas.user import ProfileUpdate

router = APIRouter(route_class=LoggingRoute, prefix="/ho-so")

@router.get("/ca-nhan", response_model=APIResponse[Any])
async def get_my_profile(current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await UserService.get_user_profile(current_user.id), message="Lấy hồ sơ thành công")

@router.put("/ca-nhan", response_model=APIResponse[Any])
async def update_my_profile(data: ProfileUpdate, current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await UserService.update_profile(current_user.id, data.model_dump(exclude_unset=True)), message="Cập nhật hồ sơ thành công")
