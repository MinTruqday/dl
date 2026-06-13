from typing import Any, List, Optional

from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends, HTTPException
from src.schemas.wallet_schema import CouponCreateRequest
from src.services.coupon_service import CouponService

router = APIRouter(prefix="/coupon")


@router.get("/check", response_model=APIResponse[Any])
async def validate_coupon(
    code: str,
    document_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CouponService.validate_coupon(code, db=db),
        message="Đã kiểm tra mã quà tặng",
    )


@router.get("", response_model=APIResponse[Any])
async def get_coupons(
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CouponService.get_coupons(db=db),
        message="Đã tải danh sách mã quà tặng",
    )


@router.post("", response_model=APIResponse[Any])
async def create_coupon(
    data: CouponCreateRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CouponService.create_coupon(data.model_dump(), current_user, db=db),
        message="Đã tạo mã quà tặng mới",
        status=201,
    )


@router.post("/{coupon_id}/approve", response_model=APIResponse[Any])
async def approve_coupon(
    coupon_id: str,
    action: str = "approve",
    current_user: UserInDB = Depends(require_role([RoleEnum.ADMIN])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CouponService.approve_coupon(coupon_id, action, current_user, db=db),
        message="Đã phê duyệt mã quà tặng",
    )


@router.patch("/{coupon_id}/status", response_model=APIResponse[Any])
async def toggle_coupon_status(
    coupon_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CouponService.update_status(coupon_id, current_user, db=db),
        message="Đã cập nhật trạng thái",
    )


@router.delete("/{coupon_id}", response_model=APIResponse[Any])
async def delete_coupon(
    coupon_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CouponService.delete_coupon(coupon_id, current_user, db=db),
        message="Đã xóa mã quà tặng",
    )
