from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.services.coupon import CouponManager

from core.dependency import get_db, require_role
from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB

router = APIRouter(prefix="/coupons")


class CouponCreateRequest(BaseModel):
    code: str
    discount_percent: float
    max_uses: int
    expires_at: str


@router.post(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def create_coupon(req: CouponCreateRequest, db=Depends(get_db)):
    return APIResponse(
        data=await CouponManager.create_coupon(req.model_dump(), db=db),
        message="Tạo mã giảm giá thành công",
        status=201,
    )


@router.get(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_all_coupons(db=Depends(get_db)):
    return APIResponse(
        data=await CouponManager.get_all_coupons(db=db),
        message="Lấy danh sách mã giảm giá thành công",
        status=200,
    )


@router.delete(
    "/{coupon_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def delete_coupon(coupon_id: str, db=Depends(get_db)):
    return APIResponse(
        data=await CouponManager.delete_coupon(coupon_id, db=db),
        message="Xóa vĩnh viễn mã giảm giá thành công",
        status=200,
    )
