from typing import Any, List
from fastapi import APIRouter, Depends
from api.dependencies import require_role
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.subscription import SubscriptionService
from pydantic import BaseModel

router = APIRouter(prefix="/subscriptions")

class SubscriptionPlanRequest(BaseModel):
    name: str
    description: str = ""
    price_dl: int = 0
    benefits: List[str] = []

class TipRequest(BaseModel):
    amount: int
    message: str = ""

@router.post("/plans", response_model=APIResponse[Any])
async def create_subscription_plan(data: SubscriptionPlanRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await SubscriptionService.create_subscription_plan(data.model_dump(), current_user),
        message="Tạo gói hội viên thành công.",
        status=201
    )

@router.get("/plans/{author_id}", response_model=APIResponse[Any])
async def get_author_plans(author_id: str):
    return APIResponse(
        data=await SubscriptionService.get_author_plans(author_id),
        message="Lấy danh sách gói hội viên thành công."
    )

@router.post("/subscribe/{plan_id}", response_model=APIResponse[Any])
async def subscribe_to_author(plan_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.READER, RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await SubscriptionService.subscribe_to_author(plan_id, current_user),
        message="Đăng ký hội viên thành công."
    )

@router.post("/tip/{author_id}", response_model=APIResponse[Any])
async def tip_author(author_id: str, data: TipRequest, current_user: UserInDB = Depends(require_role([RoleEnum.READER, RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await SubscriptionService.tip_author(author_id, data.amount, current_user, data.message),
        message="Gửi ủng hộ thành công."
    )
