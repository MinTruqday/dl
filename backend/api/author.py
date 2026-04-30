from typing import Any
from core.response import APIResponse
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
    email: str
    role: str = "editor"

class ReviewReplyRequest(BaseModel):
    reply_text: str

class VersionSaveRequest(BaseModel):
    note: str = "Tự động lưu"

class FlashSaleRequest(BaseModel):
    price: float
    expires_at: str

@router.get("/documents", response_model=APIResponse[Any])
async def get_my_documents(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.get_my_documents(current_user, skip, limit), message="Lấy danh sách tài liệu của bạn thành công.", status=200)

@router.put("/documents/{document_id}/pricing", response_model=APIResponse[Any])
async def set_document_pricing(document_id: str, data: DocumentPricingRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.set_document_pricing(document_id, data.model_dump(), current_user), message="Cập nhật giá bán tài liệu thành công.", status=200)

@router.get("/revenue", response_model=APIResponse[Any])
async def get_revenue_analytics(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.get_revenue_analytics(current_user), message="Lấy số liệu doanh thu thành công.", status=200)

@router.get("/documents/{document_id}/feedback", response_model=APIResponse[Any])
async def get_reader_feedback(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.get_reader_feedback(document_id, current_user), message="Lấy phản hồi của độc giả thành công.", status=200)

@router.post("/coupons", response_model=APIResponse[Any])
async def create_coupon(data: CouponCreateRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.create_coupon(data.model_dump(), current_user), message="Tạo mã giảm giá thành công.", status=201)

@router.get("/coupons", response_model=APIResponse[Any])
async def get_my_coupons(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.get_my_coupons(current_user), message="Lấy danh sách mã giảm giá thành công.", status=200)

@router.patch("/coupons/{coupon_id}/toggle", response_model=APIResponse[Any])
async def toggle_coupon_status(coupon_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.toggle_coupon_status(coupon_id, current_user), message="Cập nhật trạng thái thành công.", status=200)

@router.delete("/coupons/{coupon_id}", response_model=APIResponse[Any])
async def delete_coupon(coupon_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.delete_coupon(coupon_id, current_user), message="Xóa mã giảm giá thành công.", status=200)

@router.get("/documents/{document_id}/dropoff", response_model=APIResponse[Any])
async def get_chapter_dropoff(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.get_chapter_dropoff(document_id, current_user), message="Lấy tỷ lệ rời bỏ của chương thành công.", status=200)

@router.post("/series", response_model=APIResponse[Any])
async def create_series(data: SeriesCreateRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.create_series(data.model_dump(), current_user), message="Tạo bộ sưu tập tài liệu thành công.", status=201)

@router.get("/series", response_model=APIResponse[Any])
async def get_my_series(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.get_my_series(current_user), message="Lấy danh sách bộ sưu tập thành công.", status=200)

@router.put("/brand", response_model=APIResponse[Any])
async def update_brand_page(data: BrandPageRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.update_brand_page(data.model_dump(), current_user), message="Cập nhật trang thương hiệu thành công.", status=200)

@router.put("/documents/{document_id}/password", response_model=APIResponse[Any])
async def set_document_password(document_id: str, data: DocumentPasswordRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.set_document_password(document_id, data.password, current_user), message="Thiết lập mật khẩu bảo vệ tài liệu thành công.", status=200)

@router.post("/payout", response_model=APIResponse[Any])
async def request_payout(data: PayoutRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.request_payout(data.model_dump(), current_user), message="Gửi yêu cầu rút tiền thành công.", status=201)

@router.get("/documents/{document_id}/sentiment", response_model=APIResponse[Any])
async def analyze_reader_sentiment(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.analyze_reader_sentiment(document_id, current_user), message="Phân tích cảm xúc độc giả thành công.", status=200)

@router.post("/documents/{document_id}/grammar/{chapter_id}", response_model=APIResponse[Any])
async def check_grammar(document_id: str, chapter_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.check_grammar(document_id, chapter_id, current_user), message="Kiểm tra ngữ pháp chương tài liệu thành công.", status=200)

@router.post("/documents/{document_id}/generate-cover", response_model=APIResponse[Any])
async def generate_cover(document_id: str, data: CoverGenerateRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.generate_cover(document_id, data.style, current_user), message="Tạo bìa tài liệu tự động thành công.", status=201)

@router.get("/assets", response_model=APIResponse[Any])
async def get_assets(asset_type: str = Query("all"), current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.get_assets(current_user, asset_type), message="Lấy danh sách tài nguyên thành công.", status=200)

@router.post("/assets", response_model=APIResponse[Any])
async def upload_asset(data: AssetUploadRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.upload_asset(data.model_dump(), current_user), message="Tải lên tài nguyên thành công.", status=201)

@router.delete("/assets/{asset_id}", response_model=APIResponse[Any])
async def delete_asset(asset_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.delete_asset(asset_id, current_user), message="Xóa tài nguyên thành công.", status=200)

@router.post("/documents/{document_id}/versions", response_model=APIResponse[Any])
async def save_document_version(document_id: str, data: VersionSaveRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await VersionsService.save_version(document_id, data.note, current_user), message="Lưu phiên bản tài liệu thành công.", status=201)

@router.get("/documents/{document_id}/versions", response_model=APIResponse[Any])
async def get_document_versions(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await VersionsService.get_versions(document_id, current_user), message="Lấy lịch sử phiên bản thành công.", status=200)

@router.post("/versions/{version_id}/restore", response_model=APIResponse[Any])
async def restore_document_version(version_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await VersionsService.restore_version(version_id, current_user), message="Khôi phục phiên bản tài liệu thành công.", status=200)

@router.post("/documents/{document_id}/coauthors", response_model=APIResponse[Any])
async def invite_coauthor(document_id: str, data: CoauthorInviteRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.send_collaboration_invite(document_id, data.email, data.role, current_user), message="Gửi lời mời đồng tác giả thành công.", status=201)

@router.get("/collaboration/invites", response_model=APIResponse[Any])
async def get_collaboration_invites(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await AuthorService.get_my_collaboration_invites(current_user), message="Lấy danh sách lời mời thành công.", status=200)

@router.post("/collaboration/respond/{invite_id}", response_model=APIResponse[Any])
async def respond_to_invite(invite_id: str, status: str = Query(...), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await AuthorService.respond_to_collaboration_invite(invite_id, status, current_user), message="Xử lý lời mời thành công.", status=200)

@router.post("/reviews/{review_id}/reply", response_model=APIResponse[Any])
async def reply_to_review(review_id: str, data: ReviewReplyRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.reply_to_review(review_id, data.reply_text, current_user), message="Phản hồi đánh giá thành công.", status=201)

@router.delete("/documents/{document_id}", response_model=APIResponse[Any])
async def soft_delete_document(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.soft_delete_document(document_id, current_user), message="Đã chuyển tài liệu vào thùng rác.", status=200)

@router.post("/documents/{document_id}/restore", response_model=APIResponse[Any])
async def restore_document(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.restore_document(document_id, current_user), message="Khôi phục tài liệu từ thùng rác thành công.", status=200)

@router.get("/trash", response_model=APIResponse[Any])
async def get_trash(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.get_trash(current_user), message="Lấy danh sách tài liệu trong thùng rác thành công.", status=200)

@router.put("/documents/{document_id}/free-preview", response_model=APIResponse[Any])
async def set_free_preview(document_id: str, data: FreePreviewRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.set_free_preview(document_id, data.chapter_ids, current_user), message="Thiết lập chương đọc thử miễn phí thành công.", status=200)

@router.post("/documents/{document_id}/schedule", response_model=APIResponse[Any])
async def schedule_publish(document_id: str, data: SchedulePublishRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.schedule_publish(document_id, data.publish_at, current_user), message="Hẹn giờ xuất bản tài liệu thành công.", status=201)

@router.post("/reviews/{review_id}/pin", response_model=APIResponse[Any])
async def pin_review(review_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.pin_review(review_id, current_user), message="Ghim đánh giá nổi bật thành công.", status=200)

@router.get("/fans/top", response_model=APIResponse[Any])
async def get_top_fans(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.get_top_fans(current_user), message="Lấy danh sách người hâm mộ hàng đầu thành công.", status=200)

@router.get("/blocked-users", response_model=APIResponse[Any])
async def get_blocked_users(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.get_blocked_users(current_user), message="Lấy danh sách người dùng đã chặn thành công.", status=200)

@router.post("/blocked-users/{user_id}", response_model=APIResponse[Any])
async def block_user(user_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.block_user(user_id, current_user), message="Chặn người dùng thành công.", status=200)

@router.delete("/blocked-users/{user_id}", response_model=APIResponse[Any])
async def unblock_user(user_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.unblock_user(user_id, current_user), message="Bỏ chặn người dùng thành công.", status=200)

@router.post("/documents/{document_id}/flash-sale", response_model=APIResponse[Any])
async def set_flash_sale(document_id: str, data: FlashSaleRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.set_flash_sale(document_id, data.model_dump(), current_user), message="Thiết lập chương trình Flash Sale thành công.", status=201)

@router.get("/documents/{document_id}/conversion", response_model=APIResponse[Any])
async def get_conversion_rate(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.get_conversion_rate(document_id, current_user), message="Lấy tỷ lệ chuyển đổi thành công.", status=200)

@router.get("/documents/{document_id}/buyers", response_model=APIResponse[Any])
async def get_buyer_list(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(data=await AuthorService.get_buyer_list(document_id, current_user), message="Lấy danh sách người mua tài liệu thành công.", status=200)
