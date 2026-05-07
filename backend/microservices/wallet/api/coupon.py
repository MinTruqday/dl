from typing import Any, Optional
from fastapi import APIRouter, Depends
from api.dependency import require_role
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.coupon import CouponService
from pydantic import BaseModel
router = APIRouter(prefix="/ma-giam-gia")
class CouponCreateRequest(BaseModel):
    code: str
    discount_percent: int = 10
    max_uses: int = 100
    document_id: Optional[str] = None
    expires_at: Optional[str] = None
@router.post("", response_model=APIResponse[Any])
async def create_coupon(data: CouponCreateRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CouponService.create_coupon(data.model_dump(), current_user),
        message="Tạo mã giảm giá thành công",
        status=201
    )
@router.get("", response_model=APIResponse[Any])
async def get_my_coupons(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CouponService.get_my_coupons(current_user),
        message="Lấy danh sách mã giảm giá thành công"
    )
@router.patch("/{coupon_id}/trang-thai", response_model=APIResponse[Any])
async def toggle_coupon_status(coupon_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CouponService.toggle_coupon_status(coupon_id, current_user),
        message="Cập nhật trạng thái thành công"
    )
@router.delete("/{coupon_id}", response_model=APIResponse[Any])
async def delete_coupon(coupon_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await CouponService.delete_coupon(coupon_id, current_user),
        message="Xóa mã giảm giá thành công"
    )
