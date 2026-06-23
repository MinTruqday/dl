from typing import Any

from fastapi import APIRouter, Depends
from src.schemas.content_monetization import PurchaseRequest, MembershipRequest
from src.services.pricing_strategy import PricingStrategy
from src.services.document_purchases import PurchaseProcess

from shared.dependencies import get_current_user, get_db
from shared.responses import APIResponse
from shared.dependencies import CurrentUser, RoleEnum

router = APIRouter(prefix="/kiem-tien")


@router.post("/mua/tai-lieu", response_model=APIResponse[Any])
async def purchase_document(
    req: PurchaseRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PurchaseProcess.purchase_document(
            req.document_id, current_user, db=db
        ),
        message="Thanh toán mua tài liệu thành công",
        status=200,
    )


@router.post("/thanh-vien", response_model=APIResponse[Any])
async def buy_membership(
    req: MembershipRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PurchaseProcess.buy_ai_tier(req.tier, current_user, db=db),
        message="Nâng cấp gói thành viên thành công",
        status=200,
    )


@router.get("/bang-gia", response_model=APIResponse[Any])
async def get_pricing_config(db=Depends(get_db)):
    return APIResponse(
        data=await PricingStrategy.get_pricing_config(db=db),
        message="Lấy giá gói thành viên thành công",
        status=200,
    )


@router.get("/doanh-thu", response_model=APIResponse[Any])
async def get_author_revenue(current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)):
    revenue_data = await PurchaseProcess.get_author_revenue(current_user, db=db)
    return APIResponse(
        data=revenue_data,
        message="Lấy số liệu doanh thu thành công",
        status=200
    )


from pydantic import BaseModel

class PricingUpdate(BaseModel):
    document_id: str
    price_dl: float
    is_drm_protected: bool = True

@router.put("/thiet-lap-gia", response_model=APIResponse[Any])
async def set_document_pricing(
    req: PricingUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db)
):
    from fastapi import HTTPException
    from shared.repositories.base_repository import RepositoryFactory
    
    doc = await RepositoryFactory.get("documents").find_one({"_id": req.document_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
    if doc.get("creator_id") != str(current_user.id) and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Chỉ tác giả mới được thay đổi giá bán")
        
    await RepositoryFactory.get("documents").update_one(
        {"_id": req.document_id},
        {"$set": {
            "price_dl": req.price_dl, 
            "is_drm_protected": req.is_drm_protected,
            "is_premium": req.price_dl > 0
        }}
    )

    return APIResponse(
        data={"document_id": req.document_id, "price_dl": req.price_dl, "is_drm_protected": req.is_drm_protected},
        message="Cập nhật giá bán thành công",
        status=200
    )

