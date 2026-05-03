from typing import Any, List, Optional
from core.response import APIResponse
from fastapi import APIRouter, Depends
from api.dependency import get_current_user, require_role
from models.user import UserInDB, RoleEnum
from services.monetization import MonetizationService
from pydantic import BaseModel

router = APIRouter(prefix="/monetization")

class PlanCreate(BaseModel):
    name: str
    description: str
    price_dl: int
    benefits: List[str]

class TipRequest(BaseModel):
    author_id: str
    amount: int
    message: Optional[str] = ""

@router.post("/plans", response_model=APIResponse[Any])
async def create_plan(plan: PlanCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await MonetizationService.create_subscription_plan(plan.model_dump(), current_user), 
        message="Tạo gói hội viên thành công.", 
        status=201
    )

@router.get("/plans/{author_id}", response_model=APIResponse[Any])
async def get_plans(author_id: str):
    return APIResponse(
        data=await MonetizationService.get_author_plans(author_id), 
        message="Lấy danh sách gói hội viên thành công."
    )

@router.post("/subscribe/{plan_id}", response_model=APIResponse[Any])
async def subscribe(plan_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await MonetizationService.subscribe_to_author(plan_id, current_user), 
        message="Đăng ký hội viên thành công."
    )

@router.post("/tip", response_model=APIResponse[Any])
async def tip(req: TipRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await MonetizationService.tip_author(req.author_id, req.amount, current_user, req.message), 
        message="Ủng hộ tác giả thành công."
    )

class DocumentPricingRequest(BaseModel):
    price_dl: int = 0
    is_drm_protected: bool = True

class FlashSaleRequest(BaseModel):
    price: float
    expires_at: str

@router.put("/documents/{document_id}/pricing", response_model=APIResponse[Any])
async def set_document_pricing(document_id: str, data: DocumentPricingRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await MonetizationService.set_document_pricing(document_id, data.model_dump(), current_user),
        message="Cập nhật giá bán thành công."
    )

@router.post("/documents/{document_id}/flash-sale", response_model=APIResponse[Any])
async def set_flash_sale(document_id: str, data: FlashSaleRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await MonetizationService.set_flash_sale(document_id, data.model_dump(), current_user),
        message="Thiết lập Flash Sale thành công."
    )

@router.get("/analytics/revenue", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_author_revenue(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await MonetizationService.get_author_revenue_analytics(current_user),
        message="Lấy số liệu doanh thu thành công."
    )
