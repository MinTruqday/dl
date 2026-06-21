from typing import Any

from fastapi import APIRouter, Depends, Query
from src.schemas.fiat_withdrawal import WithdrawalRequest
from src.services.withdrawal import FiatWithdrawal

from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from core.dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/rut-tien")


@router.post("", response_model=APIResponse[Any])
async def request_withdrawal(
    req: WithdrawalRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await FiatWithdrawal.request_withdrawal(req, current_user, db=db),
        message="Đã gửi yêu cầu rút tiền",
        status=201,
    )


@router.get(
    "/hang-doi",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_withdrawal_queue(
    status: str = "PENDING", limit: int = 50, db=Depends(get_db)
):
    return APIResponse(
        data=await FiatWithdrawal.get_withdrawal_queue(status, limit, db=db),
        message="Lấy danh sách giao dịch rút tiền thành công",
        status=200,
    )


@router.post(
    "/{withdrawal_id}/xac-minh",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def verify_withdrawal(
    withdrawal_id: str,
    action: str,
    reason: str = "",
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await FiatWithdrawal.verify_withdrawal(
            withdrawal_id, action, reason, current_user, db=db
        ),
        message="Xác minh yêu cầu rút tiền thành công",
        status=200,
    )
