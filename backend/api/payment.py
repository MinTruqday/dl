from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.dependencies import get_current_user
from models.user import UserInDB
from services.payment import PaymentService

router = APIRouter()

class PurchaseUnlockRequest(BaseModel):
    document_id: str
    chapter_id: str

@router.post("/purchase-chapter")
async def purchase_chapter(req: PurchaseUnlockRequest, current_user: UserInDB = Depends(get_current_user)):
    return await PaymentService.purchase_chapter(req, current_user)

@router.post("/deposit")
async def deposit_fiat(amount_vnd: int, current_user: UserInDB = Depends(get_current_user)):
    return await PaymentService.deposit_fiat(amount_vnd, current_user)
