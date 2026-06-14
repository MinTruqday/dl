from typing import Any

from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends, Query
from src.schemas.withdrawal_schema import WithdrawalRequest
from src.services.withdrawal_service import WithdrawalService

router = APIRouter(prefix="/withdrawals")


@router.post("", response_model=APIResponse[Any])
async def request_withdrawal(
    req: WithdrawalRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await WithdrawalService.request_withdrawal(req, current_user, db=db),
        message="The withdrawal request has been successfully submitted and is currently pending administrative review",
        status=201,
    )


@router.get(
    "/queue",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_withdrawal_queue(
    status: str = "PENDING", limit: int = 50, db=Depends(get_db)
):
    return APIResponse(
        data=await WithdrawalService.get_withdrawal_queue(status, limit, db=db),
        message="The requested list of financial withdrawal transactions has been successfully retrieved from the system",
        status=200,
    )


@router.post(
    "/{withdrawal_id}/verify",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def verify_withdrawal(
    withdrawal_id: str,
    action: str,
    reason: str = "",
    current_admin: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await WithdrawalService.verify_withdrawal(
            withdrawal_id, action, reason, current_admin, db=db
        ),
        message="The administrative verification process for the specified withdrawal request has been completed successfully",
        status=200,
    )