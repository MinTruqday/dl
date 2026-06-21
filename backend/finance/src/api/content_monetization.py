from typing import Any

from fastapi import APIRouter, Depends
from src.schemas.content_monetization import PurchaseRequest, MembershipRequest
from src.services.pricing_strategy import PricingStrategy
from src.services.document_purchase import PurchaseProcess

from core.system_dependency import get_current_user, get_db
from core.api_response import APIResponse
from core.system_dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/kiem-tien")


@router.post("/mua/tai-lieu", response_model=APIResponse[Any])
async def purchase_document(
    req: PurchaseRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PurchaseProcess.purchase_document(
            req.document_id, current_user, db=db
        ),
        message="Thanh toán mua tài liệu thành công",
        status=200,
    )


@router.post("/thanh-vien", response_model=APIResponse[Any])
async def buy_membership(
    req: MembershipRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PurchaseProcess.buy_ai_tier(req.tier, current_user, db=db),
        message="Nâng cấp gói thành viên thành công",
        status=200,
    )


@router.get("/bang-gia", response_model=APIResponse[Any])
async def get_pricing_config(db=Depends(get_db)):
    return APIResponse(
        data=await PricingStrategy.get_pricing_config(db=db),
        message="Lấy giá gói thành viên thành công",
        status=200,
    )
