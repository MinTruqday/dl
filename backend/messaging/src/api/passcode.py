from typing import Any
from fastapi import APIRouter, Depends
from src.core.logging_route import LoggingRoute
from src.core.dependency import get_current_user
from src.core.response import APIResponse
from src.services.passcode import PasscodeService

router = APIRouter(route_class=LoggingRoute, prefix="/tin-nhan")

@router.post("/{other_user_id}/an-tin-nhan", response_model=APIResponse[Any])
async def set_pin_lock(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    pin_code = req.get("pin_code", "")
    result = await PasscodeService.set_pin_lock(other_user_id, pin_code, current_user)
    return APIResponse(data=result, message="Đặt mã PIN ẩn cuộc trò chuyện thành công")

@router.post("/{other_user_id}/xac-thuc-pin", response_model=APIResponse[Any])
async def verify_pin(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    pin_code = req.get("pin_code", "")
    result = await PasscodeService.verify_pin(other_user_id, pin_code, current_user)
    return APIResponse(data=result, message="Xác thực mã PIN thành công")

@router.post("/{other_user_id}/xoa-ma-pin", response_model=APIResponse[Any])
async def remove_pin_lock(other_user_id: str, req: dict, current_user=Depends(get_current_user)):
    pin_code = req.get("pin_code", "")
    result = await PasscodeService.remove_pin_lock(other_user_id, pin_code, current_user)
    return APIResponse(data=result, message="Xóa mã PIN ẩn cuộc trò chuyện thành công")
