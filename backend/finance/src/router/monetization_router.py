from typing import Any

from core.dependency import get_current_user, get_db
from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.services.pricing_service import PricingService
from src.services.purchase_service import PurchaseService

router = APIRouter(prefix="/monetization")


class PurchaseRequest(BaseModel):
    document_id: str
    coupon_code: str = None


class MembershipRequest(BaseModel):
    tier: str


@router.post("/purchase/document", response_model=APIResponse[Any])
async def purchase_document(
    req: PurchaseRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PurchaseService.purchase_document(
            req.document_id, req.coupon_code, current_user, db=db
        ),
        message="Thanh toán mua tài liệu thành công",
        status=200,
    )


@router.post("/membership", response_model=APIResponse[Any])
async def buy_membership(
    req: MembershipRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PurchaseService.buy_ai_tier(req.tier, current_user, db=db),
        message="Nâng cấp gói thành viên thành công",
        status=200,
    )


@router.get("/pricing", response_model=APIResponse[Any])
async def get_pricing_config(db=Depends(get_db)):
    return APIResponse(
        data=await PricingService.get_pricing_config(db=db),
        message="Lấy cấu hình giá gói thành viên thành công",
        status=200,
    )