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

@router.get("/cai-dat", response_model=APIResponse[Any])
async def get_my_settings(current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)):
    profile = await UserService.get_user_profile(current_user.id)
    return APIResponse(data=profile.get("settings", {}), message="Lấy cài đặt thành công")

@router.put("/cai-dat", response_model=APIResponse[Any])
async def update_my_settings(data: dict, current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)):
    profile = await UserService.get_user_profile(current_user.id)
    settings = profile.get("settings", {})
    settings.update(data)
    updated = await UserService.update_profile(current_user.id, {"settings": settings})
    return APIResponse(data=updated.get("settings", {}), message="Cập nhật cài đặt thành công")

@router.post("/tac-gia/ung-tuyen", response_model=APIResponse[Any])
async def apply_author(data: dict, current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)):
    updated = await UserService.update_profile(current_user.id, {"author_status": "pending", "author_motivation": data.get("motivation"), "author_portfolio": data.get("portfolio")})
    return APIResponse(data=updated, message="Gửi đơn ứng tuyển tác giả thành công")

@router.delete("/xoa-tai-khoan", response_model=APIResponse[Any])
async def delete_account(current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)):
    await UserService.update_user_status(current_user.id, False)
    return APIResponse(data={}, message="Tài khoản đã được xóa")
