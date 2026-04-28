from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_current_user
from models.user import UserInDB
from services.author import AuthorService
from pydantic import BaseModel
from typing import List, Optional

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
    return APIResponse(data=await AuthorService.create_subscription_plan(plan.model_dump(), current_user), message="Tạo gói đăng ký thành viên thành công.", status=201)

@router.get("/plans/{author_id}", response_model=APIResponse[Any])
async def get_plans(author_id: str):
    return APIResponse(data=await AuthorService.get_author_plans(author_id), message="Lấy danh sách gói thành viên của tác giả thành công.", status=200)

@router.post("/subscribe/{plan_id}", response_model=APIResponse[Any])
async def subscribe(plan_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await AuthorService.subscribe_to_author(plan_id, current_user), message="Đăng ký thành viên tác giả thành công.", status=200)

@router.post("/tip", response_model=APIResponse[Any])
async def tip(req: TipRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await AuthorService.tip_author(req.author_id, req.amount, current_user, req.message), message="Ủng hộ (Tip) tác giả thành công.", status=200)
