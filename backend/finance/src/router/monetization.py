from typing import Any
from core.dependency import get_current_user, get_db
from core.response import APIResponse
from fastapi import APIRouter, Depends
from src.schemas.finance import MembershipRequest, PurchaseRequest
from src.services.pricing import PricingService
from src.services.purchases import PurchaseService

router = APIRouter(prefix="/doanh-thu")

@router.post("/mua-hang/tai-lieu", response_model=APIResponse[Any])
async def purchase_document(req: PurchaseRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PurchaseService.purchase_document(req.document_id, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.post("/thanh-vien", response_model=APIResponse[Any])
async def buy_membership(req: MembershipRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PurchaseService.buy_ai_tier(req.tier, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.get("/bang-gia", response_model=APIResponse[Any])
async def get_pricing_config(db=Depends(get_db)):
    return APIResponse(
        data=await PricingService.get_pricing_config(db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )