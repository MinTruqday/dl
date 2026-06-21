from typing import Any

from fastapi import APIRouter, Depends
from src.schemas.discount_coupon import CouponCreateRequest
from src.services.discount_coupon import DiscountCoupon

from core.system_dependency import get_db, require_role, get_current_user
from core.api_response import APIResponse
from core.system_dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/ma-qua-tang")


@router.post(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def create_coupon(
    req: CouponCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db)
):
    return APIResponse(
        data=await DiscountCoupon.create_coupon(req.model_dump(), current_user, db=db),
        message="Tạo mã giảm giá thành công",
        status=201,
    )


@router.get(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_all_coupons(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await DiscountCoupon.get_coupons(current_user, db=db),
        message="Lấy danh sách mã giảm giá thành công",
        status=200,
    )


@router.delete(
    "/{coupon_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def delete_coupon(
    coupon_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DiscountCoupon.delete_coupon(coupon_id, current_user, db=db),
        message="Xóa vĩnh viễn mã giảm giá thành công",
        status=200,
    )
