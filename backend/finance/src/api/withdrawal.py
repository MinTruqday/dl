from typing import Any

from core.dependency import get_current_user, get_db, require_role
from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends
from src.schemas.withdrawal import WithdrawalRequest
from src.services.withdrawal import WithdrawalService

router = APIRouter(prefix="/rut-tien")


@router.post(
    "",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR]))],
)
async def request_withdrawal(
    data: WithdrawalRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await WithdrawalService.create_withdrawal_request(
            data.model_dump(), current_user, db=db
        ),
        message="Đã gửi yêu cầu rút tiền",
        status=201,
    )


@router.get(
    "/hang-doi",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def get_withdrawal_queue(status: str = "PENDING", db=Depends(get_db)):
    return APIResponse(
        data=await WithdrawalService.get_payout_queue(db=db),
        message="Đã lấy danh sách hàng đợi thanh toán",
    )


@router.post(
    "/{withdrawal_id}/xac-thuc",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def verify_withdrawal(
    withdrawal_id: str,
    action: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await WithdrawalService.verify_withdrawal(
            withdrawal_id, action, current_user, db=db
        ),
        message="Xử lý thanh toán thành công",
    )


@router.post(
    "/{withdrawal_id}/cancel",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR]))],
)
async def cancel_withdrawal(
    withdrawal_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await WithdrawalService.cancel_withdrawal(
            withdrawal_id, current_user, db=db
        ),
        message="Đã hủy lệnh rút tiền",
    )


@router.get(
    "/personal",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR]))],
)
async def get_my_withdrawals(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await WithdrawalService.get_withdrawals(current_user, db=db),
        message="Đã tải danh sách lệnh rút tiền",
    )
