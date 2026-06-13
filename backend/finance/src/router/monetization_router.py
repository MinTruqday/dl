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
from src.services.subscription_service import SubscriptionService
from src.services.pricing_service import PricingService
from src.services.withdrawal_service import WithdrawalService

router = APIRouter(prefix="/monetization")


@router.post("/membership-plan", response_model=APIResponse[Any])
async def create_plan(
    plan: PlanCreate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await SubscriptionService.create_subscription_plan(
            plan.model_dump(), current_user, db=db
        ),
        message="Đã tạo gói hội viên",
        status=201,
    )


@router.get("/goi-hoi-vien/{author_id}", response_model=APIResponse[Any])
async def get_plans(author_id: str, db=Depends(get_db)):
    from core.database import db_client

    db = db_client.mongodb.get_default_database()
    plans = await db["subscription_plans"].find({"author_id": author_id}).to_list(10)
    return APIResponse(data=plans, message="Đã tải danh sách gói hội viên")


@router.post("/register/{plan_id}", response_model=APIResponse[Any])
async def subscribe(
    plan_id: str, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await SubscriptionService.subscribe_to_author(
            plan_id, current_user, db=db
        ),
        message="Đã đăng ký gói hội viên",
    )


@router.get("/subscriptions/ca-nhan", response_model=APIResponse[Any])
async def get_my_subscriptions(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await SubscriptionService.get_my_subscriptions(current_user, db=db),
        message="Đã tải danh sách hội viên",
    )


@router.post(
    "/subscriptions/{subscription_id}/tam-dung", response_model=APIResponse[Any]
)
async def pause_subscription(
    subscription_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await SubscriptionService.pause_subscription(
            subscription_id, current_user, db=db
        ),
        message="Đã tạm dừng gói hội viên",
    )


@router.post(
    "/subscriptions/{subscription_id}/tiep-tuc", response_model=APIResponse[Any]
)
async def resume_subscription(
    subscription_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await SubscriptionService.resume_subscription(
            subscription_id, current_user, db=db
        ),
        message="Đã tiếp tục gói hội viên",
    )


@router.post("/subscriptions/{subscription_id}/huy", response_model=APIResponse[Any])
async def cancel_subscription(
    subscription_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await SubscriptionService.cancel_subscription(
            subscription_id, current_user, db=db
        ),
        message="Đã hủy gói hội viên",
    )


@router.put("/document/{document_id}/gia-ban", response_model=APIResponse[Any])
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
        message="Đã cập nhật bảng giá",
    )


@router.post("/document/{document_id}/flash-sale", response_model=APIResponse[Any])
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
        message="Đã thiết lập Flash Sale",
    )


@router.get(
    "/statistics/revenue",
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
        message="Đã tải thống kê doanh thu",
    )
