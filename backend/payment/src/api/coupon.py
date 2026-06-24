from typing import Any, Optional

from fastapi import APIRouter, Depends
from src.schemas.coupon import CouponCreateRequest
from src.services.coupon import CouponService

from src.core.dependency import get_db, require_role, get_current_user
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(prefix="/ma-qua-tang")

@router.post(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def create_coupon(
    req: CouponCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db)
):
    return APIResponse(
        data=await CouponService.create_coupon(req.model_dump(), current_user),
        message="Tạo mã giảm giá thành công",
        status=201,
    )

@router.get(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_all_coupons(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await CouponService.get_coupons(current_user),
        message="Lấy danh sách mã giảm giá thành công",
        status=200,
    )

@router.delete(
    "/{coupon_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def delete_coupon(
    coupon_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CouponService.delete_coupon(coupon_id, current_user),
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
        data=await CouponService.validate_coupon(
            code, current_user, document_id
        ),
        message="Kiểm tra mã ưu đãi thành công",
    )

@router.post(
    "/{coupon_id}/phe-duyet",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def approve_coupon(
    coupon_id: str,
    action: str = "approve",
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CouponService.approve_coupon(coupon_id, action, current_user),
        message="Xử lý phê duyệt thành công",
    )

@router.patch(
    "/{coupon_id}/trang-thai",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def toggle_coupon_status(
    coupon_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await CouponService.toggle_coupon_status(coupon_id, current_user),
        message="Cập nhật trạng thái thành công",
    )
