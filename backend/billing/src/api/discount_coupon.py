from typing import Any, Optional

from fastapi import APIRouter, Depends
from src.schemas.discount_coupon import CouponCreateRequest
from src.services.discount_coupon import DiscountCoupon

from shared.dependencies import get_db, require_role, get_current_user
from shared.responses import APIResponse
from shared.dependencies import CurrentUser, RoleEnum

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


@router.get(
    "/kiem-tra",
    response_model=APIResponse[Any],
)
async def validate_coupon(
    code: str,
    document_id: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DiscountCoupon.validate_coupon(
            code, current_user, document_id, db=db
        ),
        message="Kiểm tra mã ưu đãi thành công",
    )


@router.post(
    "/{coupon_id}/phe-duyet",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def approve_coupon(
    coupon_id: str,
    action: str = "approve",
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DiscountCoupon.approve_coupon(coupon_id, action, current_user, db=db),
        message="Xử lý phê duyệt thành công",
    )


@router.patch(
    "/{coupon_id}/trang-thai",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def toggle_coupon_status(
    coupon_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DiscountCoupon.toggle_coupon_status(coupon_id, current_user, db=db),
        message="Cập nhật trạng thái thành công",
    )
