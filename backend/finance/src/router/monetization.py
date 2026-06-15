from typing import Any
from core.dependency import get_current_user, get_db
from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends
from src.schemas.finance import MembershipRequest, PurchaseRequest
from src.services.pricing import PricingService
from src.services.purchases import PurchaseService

router = APIRouter(prefix="/monetization")

@router.post("/purchase/document", response_model=APIResponse[Any])
async def purchase_document(req: PurchaseRequest, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PurchaseService.purchase_document(req.document_id, current_user, db=db),
        message="Digital document purchase transaction has been completed successfully and library access granted",
        status=200,
    )

@router.post("/membership", response_model=APIResponse[Any])
async def buy_membership(req: MembershipRequest, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PurchaseService.buy_ai_tier(req.tier, current_user, db=db),
        message="Your artificial intelligence membership plan has been successfully upgraded and activated",
        status=200,
    )

@router.get("/pricing", response_model=APIResponse[Any])
async def get_pricing_config(db=Depends(get_db)):
    return APIResponse(
        data=await PricingService.get_pricing_config(db=db),
        message="Current membership pricing configuration matrix has been successfully retrieved from database",
        status=200,
    )