from typing import Any
from core.dependency import get_db, require_role
from core.response import APIResponse
from fastapi import APIRouter, Depends
from src.schemas.finance import CouponCreateRequest
from src.services.coupons import CouponService

router = APIRouter(prefix="/coupons")

@router.post("", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def create_coupon(req: CouponCreateRequest, db=Depends(get_db)):
    return APIResponse(
        data=await CouponService.create_coupon(req.model_dump(), current_user=None, db=db),
        message="New promotional coupon has been successfully generated and added to active marketing campaigns",
        status=201,
    )

@router.get("", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_all_coupons(db=Depends(get_db)):
    return APIResponse(
        data=await CouponService.get_coupons(current_user=None, db=db),
        message="Comprehensive list of promotional coupons has been successfully retrieved from system database",
        status=200,
    )

@router.delete("/{coupon_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def delete_coupon(coupon_id: str, db=Depends(get_db)):
    return APIResponse(
        data=await CouponService.delete_coupon(coupon_id, current_user=None, db=db),
        message="Specified promotional coupon has been permanently removed from active system records",
        status=200,
    )