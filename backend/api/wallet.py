from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends
from api.dependency import get_current_user
from models.user import UserInDB
from services.wallet import WalletService
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

@router.post("/vote", response_model=APIResponse[Any])
async def vote_item(req: VoteRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.vote_item(req, current_user), message="Bình chọn thành công.", status=200)

@router.get("/balance", response_model=APIResponse[Any])
async def get_balance(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.get_balance(current_user), message="Lấy số dư ví thành công.", status=200)

@router.post("/redeem-voucher", response_model=APIResponse[Any])
async def redeem_voucher(req: RedeemVoucherRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.redeem_voucher(req, current_user), message="Nạp voucher thành công.", status=200)

@router.get("/history", response_model=APIResponse[Any])
async def get_history(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.get_history(current_user), message="Lấy lịch sử giao dịch thành công.", status=200)

@router.post("/unlock-post", response_model=APIResponse[Any])
async def unlock_post(req: UnlockRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.unlock_post(req, current_user), message="Mở khóa bài viết thành công.", status=200)

@router.get("/top-donators", response_model=APIResponse[Any])
async def get_top_donators():
    return APIResponse(data=await WalletService.get_top_donators(), message="Lấy danh sách người ủng hộ hàng đầu thành công.", status=200)

@router.post("/tip/{target_user_id}", response_model=APIResponse[Any])
async def virtual_tip(target_user_id: str, amount: int, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.virtual_tip(target_user_id, amount, current_user), message="Gửi tiền ủng hộ thành công.", status=200)

@router.get("/revenue", response_model=APIResponse[Any])
async def get_revenue(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.get_revenue(current_user), message="Lấy số liệu doanh thu thành công.", status=200)

@router.post("/payout", response_model=APIResponse[Any])
async def request_payout(amount: int, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.request_payout(amount, current_user), message="Yêu cầu rút tiền thành công.", status=201)

from fastapi import Query as QueryParam

@router.get("/history/detailed", response_model=APIResponse[Any])
async def get_detailed_history(
    skip: int = QueryParam(0),
    limit: int = QueryParam(30),
    tx_type: str = QueryParam(None),
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await WalletService.get_detailed_history(current_user, skip, limit, tx_type), message="Lấy lịch sử giao dịch chi tiết thành công.", status=200)

@router.post("/purchase/document/{document_id}", response_model=APIResponse[Any])
async def purchase_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.purchase_document(document_id, current_user), message="Mua tài liệu thành công.", status=200)

@router.post("/purchase/chapter/{document_id}/{chapter_id}", response_model=APIResponse[Any])
async def purchase_chapter(document_id: str, chapter_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.purchase_chapter(document_id, chapter_id, current_user), message="Mua chương thành công.", status=200)
