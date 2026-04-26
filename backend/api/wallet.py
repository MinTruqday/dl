from fastapi import APIRouter, Depends
from api.dependencies import get_current_user
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

@router.post("/vote")
async def vote_item(req: VoteRequest, current_user: UserInDB = Depends(get_current_user)):
    return await WalletService.vote_item(req, current_user)

@router.get("/balance")
async def get_balance(current_user: UserInDB = Depends(get_current_user)):
    return await WalletService.get_balance(current_user)

@router.post("/redeem-voucher")
async def redeem_voucher(req: RedeemVoucherRequest, current_user: UserInDB = Depends(get_current_user)):
    return await WalletService.redeem_voucher(req, current_user)

@router.get("/history")
async def get_history(current_user: UserInDB = Depends(get_current_user)):
    return await WalletService.get_history(current_user)

@router.post("/unlock-post")
async def unlock_post(req: UnlockRequest, current_user: UserInDB = Depends(get_current_user)):
    return await WalletService.unlock_post(req, current_user)

@router.get("/top-donators")
async def get_top_donators():
    return await WalletService.get_top_donators()

@router.post("/tip/{target_user_id}")
async def virtual_tip(target_user_id: str, amount: int, current_user: UserInDB = Depends(get_current_user)):
    return await WalletService.virtual_tip(target_user_id, amount, current_user)

@router.get("/revenue")
async def get_revenue(current_user: UserInDB = Depends(get_current_user)):
    return await WalletService.get_revenue(current_user)

@router.post("/payout")
async def request_payout(amount: int, current_user: UserInDB = Depends(get_current_user)):
    return await WalletService.request_payout(amount, current_user)

from fastapi import Query as QueryParam

@router.get("/history/detailed")
async def get_detailed_history(
    skip: int = QueryParam(0),
    limit: int = QueryParam(30),
    tx_type: str = QueryParam(None),
    current_user: UserInDB = Depends(get_current_user)
):
    return await WalletService.get_detailed_history(current_user, skip, limit, tx_type)
