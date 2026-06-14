from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends
from core.dependency import get_db, get_current_user, require_role
from core.schemas.user import UserInDB, RoleEnum
from core.schemas.wallet import (
    PlanCreate,
    TipRequest,
    DocumentPricingRequest,
    FlashSaleRequest,
)
from pydantic import BaseModel
from src.services.subscription_service import SubscriptionService
from src.services.pricing_service import PricingService
from src.services.withdrawal_service import WithdrawalService

router = APIRouter(prefix="/monetization")


@router.post("/subscriptions/plans", response_model=APIResponse[Any])
async def create_plan(
    plan: PlanCreate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await SubscriptionService.create_subscription_plan(
            plan.model_dump(), current_user, db=db
        ),
        message="Subscription plan created successfully",
        status=201,
    )


@router.get("/subscriptions/plans/{author_id}", response_model=APIResponse[Any])
async def get_plans(author_id: str, db=Depends(get_db)):
    from core.database import db_client

    db = db_client.mongodb.get_default_database()
    plans = await db["subscription_plans"].find({"author_id": author_id}).to_list(10)
    return APIResponse(data=plans, message="Subscription plans retrieved successfully")


@router.post("/subscriptions/plans/{plan_id}/subscribe", response_model=APIResponse[Any])
async def subscribe(
    plan_id: str, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await SubscriptionService.subscribe_to_author(
            plan_id, current_user, db=db
        ),
        message="Successfully subscribed to plan",
    )


@router.get("/subscriptions/me", response_model=APIResponse[Any])
async def get_my_subscriptions(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await SubscriptionService.get_my_subscriptions(current_user, db=db),
        message="Subscriptions retrieved successfully",
    )


@router.post("/subscriptions/{subscription_id}/pause", response_model=APIResponse[Any])
async def pause_subscription(
    subscription_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await SubscriptionService.pause_subscription(
            subscription_id, current_user, db=db
        ),
        message="Subscription paused successfully",
    )


@router.post("/subscriptions/{subscription_id}/resume", response_model=APIResponse[Any])
async def resume_subscription(
    subscription_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await SubscriptionService.resume_subscription(
            subscription_id, current_user, db=db
        ),
        message="Subscription resumed successfully",
    )


@router.post("/subscriptions/{subscription_id}/cancel", response_model=APIResponse[Any])
async def cancel_subscription(
    subscription_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await SubscriptionService.cancel_subscription(
            subscription_id, current_user, db=db
        ),
        message="Subscription cancelled successfully",
    )


@router.put("/documents/{document_id}/pricing", response_model=APIResponse[Any])
async def set_document_pricing(
    document_id: str,
    data: DocumentPricingRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PricingService.set_document_pricing(
            document_id, data.model_dump(), current_user, db=db
        ),
        message="Pricing updated successfully",
    )


@router.post("/documents/{document_id}/flash-sale", response_model=APIResponse[Any])
async def set_flash_sale(
    document_id: str,
    data: FlashSaleRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PricingService.set_flash_sale(
            document_id, data.model_dump(), current_user, db=db
        ),
        message="Flash sale configured successfully",
    )


@router.get(
    "/revenue/statistics",
    response_model=APIResponse[Any],
    dependencies=[
        Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.MODERATOR]))
    ],
)
async def get_author_revenue(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await WithdrawalService.get_revenue(current_user, db=db),
        message="Revenue statistics retrieved successfully",
    )


class UpgradeTierRequest(BaseModel):
    tier: str


@router.post("/ai-tiers/upgrade", response_model=APIResponse[Any])
async def upgrade_ai_tier(
    req: UpgradeTierRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    from src.services.purchase_service import PurchaseService

    return APIResponse(
        data=await PurchaseService.buy_ai_tier(req.tier, current_user, db=db),
        message=f"AI tier upgraded successfully",
    )
