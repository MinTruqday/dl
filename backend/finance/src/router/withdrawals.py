from typing import Any
from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from fastapi import APIRouter, Depends
from src.schemas.finance import WithdrawalRequest
from src.services.withdrawals import WithdrawalService

router = APIRouter(prefix="/withdrawals")

@router.post("", response_model=APIResponse[Any])
async def request_withdrawal(req: WithdrawalRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await WithdrawalService.request_withdrawal(req.model_dump(), current_user, db=db),
        message="Withdrawal request has been successfully submitted and is currently pending administrative review",
        status=201,
    )

@router.get("/queue", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_withdrawal_queue(status: str = "PENDING", limit: int = 50, db=Depends(get_db)):
    return APIResponse(
        data=await WithdrawalService.get_withdrawal_queue(status, db=db),
        message="Requested list of financial withdrawal transactions has been successfully retrieved from system database",
        status=200,
    )

@router.post("/{withdrawal_id}/verify", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def verify_withdrawal(withdrawal_id: str, action: str, reason: str = "", current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await WithdrawalService.verify_withdrawal(withdrawal_id, action, current_user, db=db),
        message="Administrative verification process for specified withdrawal request has been completed successfully",
        status=200,
    )