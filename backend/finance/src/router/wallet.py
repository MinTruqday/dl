from core.config import settings
from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from src.api.dependency import get_db, get_current_user
from src.schemas.user import UserInDB
from src.services.wallet import WalletService
from src.services.purchase import PurchaseService
from src.services.withdrawal import WithdrawalService

router = APIRouter(prefix='/vi-tien')

@router.get('/so-du', response_model=APIResponse[Any])
async def get_balance(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await WalletService.get_balance(current_user, db=db), message='Lấy số dư ví success')

@router.post('/ma-qua-tang/doi-ma', response_model=APIResponse[Any])
async def redeem_coupon(req: RedeemCouponRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await WalletService.redeem_coupon(req, current_user, db=db), message='Đổi mã quà tặng success')

@router.get('/lich-su', response_model=APIResponse[Any])
async def get_history(cursor: str=Query(None), limit: int=Query(30, ge=1, le=100), tx_type: str=Query(None), skip: int=Query(0, ge=0), current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await WalletService.get_history(current_user, cursor, limit, tx_type, skip, db=db), message='Lấy lịch sử giao dịch success')



@router.get('/doanh-thu', response_model=APIResponse[Any])
async def get_revenue(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    from core.database import db_client
    db = db_client.mongodb.get_default_database()
    revenue_data = await WithdrawalService.get_revenue(current_user, db=db)
    author_id = str(current_user.id)
    docs = await db['documents'].find({'author_id': author_id, 'is_deleted': {'$ne': True}}).sort('views', -1).to_list(length=50)
    total_views = 0
    doc_list = []
    for d in docs:
        views = d.get('views', 0)
        total_views += views
        review_pipeline = [{'$match': {'document_id': str(d['_id'])}}, {'$group': {'_id': None, 'avg': {'$avg': '$rating'}}}]
        rev = await db['reviews'].aggregate(review_pipeline).to_list(length=1)
        avg_rating = rev[0]['avg'] if rev else 0
        doc_list.append({'id': str(d['_id']), 'title': d.get('title', ''), 'views': views, 'rating': round(avg_rating, 1) if avg_rating else 0, 'status': d.get('status', 'draft')})
    import httpx
    user_doc = {}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.PROVISION_URL}/nguoi-dung/noi-bo/{author_id}", timeout=3.0)
            if resp.status_code == 200:
                user_doc = resp.json().get('data') or {}
    except Exception:
        pass
        
    total_points = user_doc.get('points', 0)
    revenue_data['total_views'] = total_views
    revenue_data['total_points'] = total_points
    revenue_data['documents'] = doc_list
    
    wallet = await db['wallets'].find_one({'_id': author_id})
    revenue_data['available_balance'] = wallet.get('balance', 0) if wallet else 0
    return APIResponse(data=revenue_data, message='Lấy số liệu doanh thu success')

@router.post('/giao-dich-mua/tai-lieu/{document_id}', response_model=APIResponse[Any])
async def purchase_document(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PurchaseService.purchase_document(document_id, current_user, db=db), message='Thanh toán mua tài liệu success')

@router.post('/giao-dich-mua/{purchase_id}/huy-bo', response_model=APIResponse[Any])
async def cancel_purchase(purchase_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PurchaseService.cancel_purchase(purchase_id, current_user, db=db), message='Hủy mua success')