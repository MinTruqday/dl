from typing import Any, Literal

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Query, status
from src.schemas.withdrawal import WithdrawalRequest
from src.services.withdrawal import WithdrawalService

from src.core.dependency import get_current_user, get_db, require_role
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/rut-tien")

@router.post("", response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED)
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
    status: str = "PENDING", limit: int = Query(default=50, ge=1, le=100), db=Depends(get_db)
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
    action: Literal["approve", "reject"],
    reason: str = Query(default="", max_length=500),
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


@router.post("/{withdrawal_id}/huy", response_model=APIResponse[Any])
async def cancel_withdrawal(
    withdrawal_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await WithdrawalService.cancel_withdrawal(withdrawal_id, current_user),
        message="Hủy yêu cầu rút tiền hoàn tất",
    )
