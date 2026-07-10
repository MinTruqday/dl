from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Query
from src.schemas.withdrawal import WithdrawalRequest
from src.services.withdrawal import WithdrawalService

from src.core.dependency import get_current_user, get_db, require_role
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/rut-tien")

@router.post("", response_model=APIResponse[Any])
async def request_withdrawal(
    req: WithdrawalRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await WithdrawalService.request_withdrawal(req.model_dump(), current_user),
        message="Gửi yêu cầu khởi tạo giao dịch rút tiền hoàn tất",
        status=201,
    )

@router.get(
    "/hang-doi",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_withdrawal_queue(
    status: str = "PENDING", limit: int = 50, db=Depends(get_db)
):
    return APIResponse(
        data=await WithdrawalService.get_withdrawal_queue(status, limit),
        message="Trích xuất danh sách giao dịch rút tiền hoàn tất",
        status=200,
    )

@router.post(
    "/{withdrawal_id}/xac-minh",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def verify_withdrawal(
    withdrawal_id: str,
    action: str,
    reason: str = "",
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await WithdrawalService.verify_withdrawal(
            withdrawal_id, action, reason, current_user
        ),
        message="Xử lý xác minh yêu cầu rút tiền hoàn tất",
        status=200,
    )
