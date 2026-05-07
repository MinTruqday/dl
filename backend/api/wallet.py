from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from api.dependency import get_current_user
from models.user import UserInDB
from services.wallet import WalletService
from services.transaction import TransactionService
from pydantic import BaseModel

router = APIRouter()

class RedeemVoucherRequest(BaseModel):
    code: str

class VoteRequest(BaseModel):
    item_id: str
    item_type: str
    amount: int

class UnlockRequest(BaseModel):
    post_id: str

class PayoutRequest(BaseModel):
    amount: int

class TipRequest(BaseModel):
    amount: int

@router.post("/votes", response_model=APIResponse[Any])
async def vote_item(req: VoteRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await TransactionService.vote_item(req, current_user), message="Bình chọn thành công.", status=200)

@router.get("/balance", response_model=APIResponse[Any])
async def get_balance(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.get_balance(current_user), message="Lấy số dư ví thành công.", status=200)

@router.post("/vouchers/redemptions", response_model=APIResponse[Any])
async def redeem_voucher(req: RedeemVoucherRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.redeem_voucher(req, current_user), message="Đổi voucher thành công.", status=200)

@router.get("/history", response_model=APIResponse[Any])
async def get_history(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.get_history(current_user), message="Lấy lịch sử giao dịch thành công.", status=200)

@router.post("/unlocks", response_model=APIResponse[Any])
async def unlock_post(req: UnlockRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await TransactionService.unlock_post(req, current_user), message="Mở khóa bài viết thành công.", status=200)

@router.get("/top-donators", response_model=APIResponse[Any])
async def get_top_donators():
    return APIResponse(data=await TransactionService.get_top_donators(), message="Lấy danh sách người ủng hộ hàng đầu thành công.", status=200)

@router.post("/tips/{target_user_id}", response_model=APIResponse[Any])
async def virtual_tip(target_user_id: str, req: TipRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await TransactionService.virtual_tip(target_user_id, req.amount, current_user), message="Gửi tiền ủng hộ thành công.", status=200)

@router.get("/revenue", response_model=APIResponse[Any])
async def get_revenue(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await TransactionService.get_revenue(current_user), message="Lấy số liệu doanh thu thành công.", status=200)

@router.get("/history/detailed", response_model=APIResponse[Any])
async def get_detailed_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    tx_type: str = Query(None),
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await WalletService.get_history(current_user, skip, limit, tx_type), message="Lấy lịch sử giao dịch chi tiết thành công.", status=200)

@router.post("/purchases/documents/{document_id}", response_model=APIResponse[Any])
async def purchase_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await TransactionService.purchase_document(document_id, current_user), message="Mua tài liệu thành công.", status=200)

@router.post("/purchases/documents/{document_id}/chapters/{chapter_id}", response_model=APIResponse[Any])
async def purchase_chapter(document_id: str, chapter_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await TransactionService.purchase_chapter(document_id, chapter_id, current_user), message="Mua chương thành công.", status=200)

@router.post("/purchases/{purchase_id}/cancellation", response_model=APIResponse[Any])
async def cancel_purchase(purchase_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await TransactionService.cancel_purchase(purchase_id, current_user), message="Hủy mua thành công.", status=200)
