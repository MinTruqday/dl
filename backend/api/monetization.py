from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends
from api.dependency import get_db, get_current_user, require_role
from models.user import UserInDB, RoleEnum
from models.wallet import PlanCreate, TipRequest, DocumentPricingRequest, FlashSaleRequest
from services.subscription import SubscriptionService
from services.donation import DonationService
from services.pricing import PricingService
from services.withdrawal import WithdrawalService
router = APIRouter(prefix='/kiem-tien')

@router.post('/goi-hoi-vien', response_model=APIResponse[Any])
async def create_plan(plan: PlanCreate, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await SubscriptionService.create_subscription_plan(plan.model_dump(), current_user, db=db), message='Tạo gói hội viên thành công', status=201)

@router.get('/goi-hoi-vien/{author_id}', response_model=APIResponse[Any])
async def get_plans(author_id: str, db=Depends(get_db)):
    from core.database import db_client
    db = db_client.mongodb.get_default_database()
    plans = await db['subscription_plans'].find({'author_id': author_id}).to_list(10)
    return APIResponse(data=plans, message='Lấy danh sách gói hội viên thành công')

@router.post('/dang-ky/{plan_id}', response_model=APIResponse[Any])
async def subscribe(plan_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await SubscriptionService.subscribe_to_author(plan_id, current_user, db=db), message='Đăng ký hội viên thành công')

@router.get('/danh-sach-dang-ky/ca-nhan', response_model=APIResponse[Any])
async def get_my_subscriptions(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await SubscriptionService.get_my_subscriptions(current_user, db=db), message='Lấy danh sách hội viên thành công')

@router.post('/danh-sach-dang-ky/{subscription_id}/tam-dung', response_model=APIResponse[Any])
async def pause_subscription(subscription_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await SubscriptionService.pause_subscription(subscription_id, current_user, db=db), message='Tạm dừng hội viên thành công')

@router.post('/danh-sach-dang-ky/{subscription_id}/tiep-tuc', response_model=APIResponse[Any])
async def resume_subscription(subscription_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await SubscriptionService.resume_subscription(subscription_id, current_user, db=db), message='Tiếp tục hội viên thành công')

@router.post('/danh-sach-dang-ky/{subscription_id}/huy', response_model=APIResponse[Any])
async def cancel_subscription(subscription_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await SubscriptionService.cancel_subscription(subscription_id, current_user, db=db), message='Hủy hội viên thành công')

@router.post('/ung-ho', response_model=APIResponse[Any])
async def tip(req: TipRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    receiver = req.receiver_id or req.author_id
    if not receiver:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail='Thiếu mã người nhận (receiver_id hoặc author_id).')
    return APIResponse(data=await DonationService.virtual_tip(receiver, req.amount, current_user, req.message, db=db), message='Ủng hộ tác giả thành công')

@router.put('/tai-lieu/{document_id}/gia-ban', response_model=APIResponse[Any])
async def set_document_pricing(document_id: str, data: DocumentPricingRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PricingService.set_document_pricing(document_id, data.model_dump(), current_user, db=db), message='Cập nhật giá bán thành công')

@router.post('/tai-lieu/{document_id}/flash-sale', response_model=APIResponse[Any])
async def set_flash_sale(document_id: str, data: FlashSaleRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PricingService.set_flash_sale(document_id, data.model_dump(), current_user, db=db), message='Thiết lập Flash Sale thành công')

@router.get('/thong-ke/doanh-thu', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_author_revenue(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await WithdrawalService.get_revenue(current_user, db=db), message='Lấy số liệu doanh thu thành công')