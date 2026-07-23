from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from src.core.dependency import get_current_user
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.schemas.wallet import TransferRequest, RecipientVerifyRequest
from src.services.transfer import TransferService

router = APIRouter(route_class=LoggingRoute, prefix="/vi-tien")

@router.post("/xac-minh-nguoi-nhan", response_model=APIResponse[Any], status_code=status.HTTP_200_OK)
async def verify_recipient_info(
    req: RecipientVerifyRequest,
    current_user=Depends(get_current_user),
):
    """
    <module_purpose>Verify recipient user info (Full Name, Account Number, Email) before confirming P2P transfer.</module_purpose>
    <contract>Requires authenticated user and recipient_identifier.</contract>
    """
    result = await TransferService.verify_recipient(req.recipient_identifier)
    return APIResponse(
        data=result,
        message=f"Xác minh thông tin người nhận thành công: {result['full_name']}",
        status=status.HTTP_200_OK
    )

@router.post("/chuyen-tien", response_model=APIResponse[Any], status_code=status.HTTP_200_OK)
async def p2p_transfer_funds(
    req: TransferRequest,
    current_user=Depends(get_current_user),
):
    """
    <module_purpose>Transfer DL wallet credits to another user with Idempotency double-spend protection.</module_purpose>
    <contract>Requires authenticated current_user and valid recipient identifier + amount > 0.</contract>
    """
    result = await TransferService.transfer_funds(current_user, req)
    return APIResponse(
        data=result,
        message=f"Chuyển {req.amount} DL cho {result['recipient']['full_name']} thành công",
        status=status.HTTP_200_OK
    )
