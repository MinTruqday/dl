from typing import Any

from core.dependency import get_db, require_role
from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.services.coupon_service import CouponService

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
        data=await CouponService.create_coupon(req.model_dump(), db=db),
        message="The new promotional coupon has been successfully generated and added to the active campaigns",
        status=201,
    )


@router.get(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_all_coupons(db=Depends(get_db)):
    return APIResponse(
        data=await CouponService.get_all_coupons(db=db),
        message="The comprehensive list of promotional coupons has been successfully retrieved from the system",
        status=200,
    )


@router.delete(
    "/{coupon_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def delete_coupon(coupon_id: str, db=Depends(get_db)):
    return APIResponse(
        data=await CouponService.delete_coupon(coupon_id, db=db),
        message="The specified promotional coupon has been permanently removed from the active system records",
        status=200,
    )