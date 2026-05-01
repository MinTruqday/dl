from typing import Any, List, Optional
from core.response import APIResponse
from fastapi import APIRouter, Depends
from api.dependencies import get_current_user
from models.user import UserInDB
from services.subscription import SubscriptionService
from pydantic import BaseModel

router = APIRouter(prefix="/monetization")

class PlanCreate(BaseModel):
    name: str
    description: str
    price_dl: int
    benefits: List[str]

class TipRequest(BaseModel):
    author_id: str
    amount: int
    message: Optional[str] = ""

@router.post("/plans", response_model=APIResponse[Any])
async def create_plan(plan: PlanCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await SubscriptionService.create_subscription_plan(plan.model_dump(), current_user), 
        message="Tạo gói hội viên thành công.", 
        status=201
    )

@router.get("/plans/{author_id}", response_model=APIResponse[Any])
async def get_plans(author_id: str):
    return APIResponse(
        data=await SubscriptionService.get_author_plans(author_id), 
        message="Lấy danh sách gói hội viên thành công."
    )

@router.post("/subscribe/{plan_id}", response_model=APIResponse[Any])
async def subscribe(plan_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await SubscriptionService.subscribe_to_author(plan_id, current_user), 
        message="Đăng ký hội viên thành công."
    )

@router.post("/tip", response_model=APIResponse[Any])
async def tip(req: TipRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await SubscriptionService.tip_author(req.author_id, req.amount, current_user, req.message), 
        message="Ủng hộ tác giả thành công."
    )
