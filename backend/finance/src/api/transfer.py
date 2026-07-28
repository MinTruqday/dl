from typing import Any

from fastapi import APIRouter, Depends, status

from src.core.dependency import get_current_user
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.schemas.wallet import RecipientVerifyRequest, TransferRequest
from src.services.transfer import TransferService


router = APIRouter(route_class=LoggingRoute, prefix="/vi-tien")


@router.post(
    "/xac-minh-nguoi-nhan",
    response_model=APIResponse[Any],
    status_code=status.HTTP_200_OK,
)
async def verify_recipient_info(
    req: RecipientVerifyRequest,
    current_user=Depends(get_current_user),
):
    result = await TransferService.verify_recipient(req.recipient_identifier)
    return APIResponse(
        data=result,
        message="Xác minh người nhận hoàn tất",
        status=status.HTTP_200_OK,
    )


@router.post(
    "/chuyen-tien",
    response_model=APIResponse[Any],
    status_code=status.HTTP_200_OK,
)
async def p2p_transfer_funds(
    req: TransferRequest,
    current_user=Depends(get_current_user),
):
    result = await TransferService.transfer_funds(current_user, req)
    return APIResponse(
        data=result,
        message="Chuyển tiền hoàn tất",
        status=status.HTTP_200_OK,
    )
