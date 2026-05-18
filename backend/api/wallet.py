from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from api.dependency import get_current_user
from models.user import UserInDB
from models.wallet import RedeemVoucherRequest, VoteRequest, UnlockRequest, TipRequest
from services.wallet import WalletService
from services.donation import DonationService
from services.purchase import PurchaseService
from services.withdrawal import WithdrawalService

router = APIRouter(prefix="/vi-tien")

@router.get("/so-du", response_model=APIResponse[Any])
async def get_balance(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.get_balance(current_user), message="Lấy số dư ví thành công")

@router.post("/ma-qua-tang/doi-ma", response_model=APIResponse[Any])
async def redeem_voucher(req: RedeemVoucherRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WalletService.redeem_voucher(req, current_user), message="Đổi voucher thành công")

@router.get("/lich-su", response_model=APIResponse[Any])
async def get_history(
    cursor: str = Query(None),
    limit: int = Query(30, ge=1, le=100),
    tx_type: str = Query(None),
    skip: int = Query(0, ge=0),
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await WalletService.get_history(current_user, cursor, limit, tx_type, skip), message="Lấy lịch sử giao dịch thành công")

@router.post("/binh-chon", response_model=APIResponse[Any])
async def vote_item(req: VoteRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DonationService.vote_item(req, current_user), message="Bình chọn thành công")

@router.post("/mo-khoa", response_model=APIResponse[Any])
async def unlock_post(req: UnlockRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DonationService.unlock_post(req, current_user), message="Mở khóa bài viết thành công")

@router.post("/tien-ung-ho/{target_user_id}", response_model=APIResponse[Any])
async def virtual_tip(target_user_id: str, req: TipRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DonationService.virtual_tip(target_user_id, req.amount, current_user, req.message), message="Gửi tiền ủng hộ thành công")

@router.get("/nguoi-ung-ho-hang-dau", response_model=APIResponse[Any])
async def get_top_donators():
    return APIResponse(data=await DonationService.get_top_donators(), message="Lấy danh sách người ủng hộ hàng đầu thành công")

@router.get("/doanh-thu", response_model=APIResponse[Any])
async def get_revenue(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await WithdrawalService.get_revenue(current_user), message="Lấy số liệu doanh thu thành công")

@router.post("/giao-dich-mua/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def purchase_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PurchaseService.purchase_document(document_id, current_user), message="Mua tài liệu thành công")

@router.post("/giao-dich-mua/tai-lieu/{document_id}/chuong/{chapter_id}", response_model=APIResponse[Any])
async def purchase_chapter(document_id: str, chapter_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PurchaseService.purchase_chapter(document_id, chapter_id, current_user), message="Mua chương thành công")

@router.post("/giao-dich-mua/{purchase_id}/huy-bo", response_model=APIResponse[Any])
async def cancel_purchase(purchase_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PurchaseService.cancel_purchase(purchase_id, current_user), message="Hủy mua thành công")
