from typing import Any
from core.dependency import get_current_user, get_db
from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends
from src.schemas.finance import DepositRequest
from src.services.deposits import DepositService

router = APIRouter(prefix="/deposits")

@router.post("", response_model=APIResponse[Any])
async def create_deposit(req: DepositRequest, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await DepositService.create_deposit_link(req, current_user, db=db),
        message="Deposit transaction has been successfully initiated and is awaiting payment confirmation from gateway",
        status=201,
    )