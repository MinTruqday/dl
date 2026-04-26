from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from api.dependencies import get_current_user
from models.user import UserInDB
from services.gateway import GatewayService

router = APIRouter()

class TopupRequest(BaseModel):
    amount: int 

@router.post("/momo/create")
async def create_momo_payment(req: TopupRequest, current_user: UserInDB = Depends(get_current_user)):
    return await GatewayService.create_momo_payment(req, current_user)

@router.post("/momo/ipn")
async def momo_ipn(request: Request):
    return await GatewayService.momo_ipn(request)
