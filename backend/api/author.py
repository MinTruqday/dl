from fastapi import APIRouter, Depends, Query
from api.dependencies import get_current_user, require_role
from models.user import UserInDB, RoleEnum
from services.author import AuthorService
from services.version import VersionsService
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/author")

class DocumentPricingRequest(BaseModel):
    price_dl: int = 0
    is_drm_protected: bool = True

class SchedulePublishRequest(BaseModel):
    publish_at: str

class FreePreviewRequest(BaseModel):
    chapter_ids: List[str]

class CouponCreateRequest(BaseModel):
    code: str
    discount_percent: int = 10
    max_uses: int = 100
    document_id: Optional[str] = None
    expires_at: Optional[str] = None

class SeriesCreateRequest(BaseModel):
    title: str
    description: str = ""
    document_ids: List[str] = []

class BrandPageRequest(BaseModel):
    tagline: str = ""
    about: str = ""
    links: dict = {}

class DocumentPasswordRequest(BaseModel):
    password: str

class PayoutRequest(BaseModel):
    amount: int
    bank_info: dict

class CoverGenerateRequest(BaseModel):
    style: str = "minimalist"

class AssetUploadRequest(BaseModel):
    filename: str
    type: str = "image"
    size_bytes: int = 0
    url: str = ""

class CoauthorInviteRequest(BaseModel):
    user_id_or_email: str

class ReviewReplyRequest(BaseModel):
    reply_text: str

class VersionSaveRequest(BaseModel):
    note: str = "Tự động lưu"

@router.get("/documents")
async def get_my_documents(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.get_my_documents(current_user, skip, limit)

@router.put("/documents/{document_id}/pricing")
async def set_document_pricing(document_id: str, data: DocumentPricingRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.set_document_pricing(document_id, data.model_dump(), current_user)

@router.get("/revenue")
async def get_revenue_analytics(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.get_revenue_analytics(current_user)

@router.get("/documents/{document_id}/feedback")
async def get_reader_feedback(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.get_reader_feedback(document_id, current_user)

@router.post("/coupons")
async def create_coupon(data: CouponCreateRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.create_coupon(data.model_dump(), current_user)

@router.get("/coupons")
async def get_my_coupons(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.get_my_coupons(current_user)

@router.get("/documents/{document_id}/dropoff")
async def get_chapter_dropoff(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.get_chapter_dropoff(document_id, current_user)

@router.post("/series")
async def create_series(data: SeriesCreateRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.create_series(data.model_dump(), current_user)

@router.get("/series")
async def get_my_series(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.get_my_series(current_user)

@router.put("/brand")
async def update_brand_page(data: BrandPageRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.update_brand_page(data.model_dump(), current_user)

@router.put("/documents/{document_id}/password")
async def set_document_password(document_id: str, data: DocumentPasswordRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.set_document_password(document_id, data.password, current_user)

@router.post("/payout")
async def request_payout(data: PayoutRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.request_payout(data.model_dump(), current_user)

@router.get("/documents/{document_id}/sentiment")
async def analyze_reader_sentiment(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.analyze_reader_sentiment(document_id, current_user)

@router.post("/documents/{document_id}/grammar/{chapter_id}")
async def check_grammar(document_id: str, chapter_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.check_grammar(document_id, chapter_id, current_user)

@router.post("/documents/{document_id}/generate-cover")
async def generate_cover(document_id: str, data: CoverGenerateRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.generate_cover(document_id, data.style, current_user)

@router.get("/assets")
async def get_assets(asset_type: str = Query("all"), current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.get_assets(current_user, asset_type)

@router.post("/assets")
async def upload_asset(data: AssetUploadRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.upload_asset(data.model_dump(), current_user)

@router.delete("/assets/{asset_id}")
async def delete_asset(asset_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.delete_asset(asset_id, current_user)

@router.post("/documents/{document_id}/versions")
async def save_document_version(document_id: str, data: VersionSaveRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await VersionsService.save_version(document_id, data.note, current_user)

@router.get("/documents/{document_id}/versions")
async def get_document_versions(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await VersionsService.get_versions(document_id, current_user)

@router.post("/versions/{version_id}/restore")
async def restore_document_version(version_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await VersionsService.restore_version(version_id, current_user)

@router.post("/documents/{document_id}/coauthors")
async def invite_coauthor(document_id: str, data: CoauthorInviteRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.invite_coauthor(document_id, data.user_id_or_email, current_user)

@router.post("/reviews/{review_id}/reply")
async def reply_to_review(review_id: str, data: ReviewReplyRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.reply_to_review(review_id, data.reply_text, current_user)

@router.delete("/documents/{document_id}")
async def soft_delete_document(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.soft_delete_document(document_id, current_user)

@router.post("/documents/{document_id}/restore")
async def restore_document(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.restore_document(document_id, current_user)

@router.get("/trash")
async def get_trash(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.get_trash(current_user)

@router.put("/documents/{document_id}/free-preview")
async def set_free_preview(document_id: str, data: FreePreviewRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.set_free_preview(document_id, data.chapter_ids, current_user)

@router.post("/documents/{document_id}/schedule")
async def schedule_publish(document_id: str, data: SchedulePublishRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.schedule_publish(document_id, data.publish_at, current_user)

@router.post("/reviews/{review_id}/pin")
async def pin_review(review_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.pin_review(review_id, current_user)

@router.get("/fans/top")
async def get_top_fans(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.get_top_fans(current_user)

@router.get("/blocked-users")
async def get_blocked_users(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.get_blocked_users(current_user)

@router.post("/blocked-users/{user_id}")
async def block_user(user_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.block_user(user_id, current_user)

@router.delete("/blocked-users/{user_id}")
async def unblock_user(user_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.unblock_user(user_id, current_user)

class FlashSaleRequest(BaseModel):
    price: float
    expires_at: str

@router.post("/documents/{document_id}/flash-sale")
async def set_flash_sale(document_id: str, data: FlashSaleRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.set_flash_sale(document_id, data.model_dump(), current_user)

@router.get("/documents/{document_id}/conversion")
async def get_conversion_rate(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.get_conversion_rate(document_id, current_user)

@router.get("/documents/{document_id}/buyers")
async def get_buyer_list(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return await AuthorService.get_buyer_list(document_id, current_user)
