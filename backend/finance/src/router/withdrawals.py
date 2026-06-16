from typing import Any
from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from fastapi import APIRouter, Depends
from src.schemas.finance import WithdrawalRequest
from src.services.withdrawals import WithdrawalService

router = APIRouter(prefix="/rut-tien")

@router.post("", response_model=APIResponse[Any])
async def request_withdrawal(req: WithdrawalRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await WithdrawalService.request_withdrawal(req.model_dump(), current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=201,
    )

@router.get("/hang-doi", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_withdrawal_queue(status: str = "PENDING", limit: int = 50, db=Depends(get_db)):
    return APIResponse(
        data=await WithdrawalService.get_withdrawal_queue(status, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.post("/{withdrawal_id}/xac-minh", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def verify_withdrawal(withdrawal_id: str, action: str, reason: str = "", current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await WithdrawalService.verify_withdrawal(withdrawal_id, action, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )