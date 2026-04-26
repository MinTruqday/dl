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

@router.post("/plans")
async def create_plan(plan: PlanCreate, current_user: UserInDB = Depends(get_current_user)):
    return await AuthorService.create_subscription_plan(plan.model_dump(), current_user)

@router.get("/plans/{author_id}")
async def get_plans(author_id: str):
    return await AuthorService.get_author_plans(author_id)

@router.post("/subscribe/{plan_id}")
async def subscribe(plan_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await AuthorService.subscribe_to_author(plan_id, current_user)

@router.post("/tip")
async def tip(req: TipRequest, current_user: UserInDB = Depends(get_current_user)):
    return await AuthorService.tip_author(req.author_id, req.amount, current_user, req.message)
