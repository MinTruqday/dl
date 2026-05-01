from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from api.dependencies import require_role
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.author import AuthorService
from services.document import DocumentService
from services.editor import EditorService
from pydantic import BaseModel

router = APIRouter(prefix="/author")

class DocumentPricingRequest(BaseModel):
    price_dl: int = 0
    is_drm_protected: bool = True

class SchedulePublishRequest(BaseModel):
    publish_at: str

class FreePreviewRequest(BaseModel):
    chapter_ids: List[str]

class SeriesCreateRequest(BaseModel):
    title: str
    description: str = ""
    document_ids: List[str] = []

class BrandPageRequest(BaseModel):
    tagline: str = ""
    about: str = ""
    links: dict = {}
    welcome_message: str = ""

class DocumentPasswordRequest(BaseModel):
    password: str

class FlashSaleRequest(BaseModel):
    price: float
    expires_at: str

class ReviewReplyRequest(BaseModel):
    reply_text: str

@router.get("/documents", response_model=APIResponse[Any])
async def get_my_documents(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await DocumentService.get_my_documents(current_user, skip, limit),
        message="Lấy danh sách tài liệu thành công."
    )

@router.put("/documents/{document_id}/pricing", response_model=APIResponse[Any])
async def set_document_pricing(document_id: str, data: DocumentPricingRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await DocumentService.set_document_pricing(document_id, data.model_dump(), current_user),
        message="Cập nhật giá bán thành công."
    )

@router.post("/documents/{document_id}/schedule", response_model=APIResponse[Any])
async def schedule_publish(document_id: str, data: SchedulePublishRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await DocumentService.schedule_publish(document_id, data.publish_at, current_user),
        message="Lên lịch xuất bản thành công."
    )

@router.put("/documents/{document_id}/preview", response_model=APIResponse[Any])
async def set_free_preview(document_id: str, data: FreePreviewRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await DocumentService.set_free_preview(document_id, data.chapter_ids, current_user),
        message="Thiết lập chương đọc thử thành công."
    )

@router.delete("/documents/{document_id}", response_model=APIResponse[Any])
async def soft_delete_document(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await DocumentService.soft_delete_document(document_id, current_user),
        message="Đã chuyển tài liệu vào thùng rác."
    )

@router.post("/documents/{document_id}/restore", response_model=APIResponse[Any])
async def restore_document(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await DocumentService.restore_document(document_id, current_user),
        message="Khôi phục tài liệu thành công."
    )

@router.get("/trash", response_model=APIResponse[Any])
async def get_trash(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await DocumentService.get_trash(current_user),
        message="Lấy danh sách thùng rác thành công."
    )

@router.post("/documents/{document_id}/password", response_model=APIResponse[Any])
async def set_document_password(document_id: str, data: DocumentPasswordRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await DocumentService.set_document_password(document_id, data.password, current_user),
        message="Thiết lập mật khẩu thành công."
    )

@router.post("/series", response_model=APIResponse[Any])
async def create_series(data: SeriesCreateRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await DocumentService.create_series(data.model_dump(), current_user),
        message="Tạo Series thành công.",
        status=201
    )

@router.put("/profile/brand", response_model=APIResponse[Any])
async def update_brand_page(data: BrandPageRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await AuthorService.update_brand_page(data.model_dump(), current_user),
        message="Cập nhật trang thương hiệu thành công."
    )

@router.post("/reviews/{review_id}/reply", response_model=APIResponse[Any])
async def reply_to_review(review_id: str, data: ReviewReplyRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await AuthorService.reply_to_review(review_id, data.reply_text, current_user),
        message="Gửi phản hồi thành công."
    )

@router.post("/documents/{document_id}/flash-sale", response_model=APIResponse[Any])
async def set_flash_sale(document_id: str, data: FlashSaleRequest, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await DocumentService.set_flash_sale(document_id, data.model_dump(), current_user),
        message="Thiết lập Flash Sale thành công."
    )

@router.get("/documents/{document_id}/grammar/{chapter_id}", response_model=APIResponse[Any])
async def check_grammar(document_id: str, chapter_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await EditorService.check_grammar(document_id, chapter_id, current_user),
        message="Kiểm tra ngữ pháp hoàn tất."
    )

@router.post("/documents/{document_id}/cover/generate", response_model=APIResponse[Any])
async def generate_cover(document_id: str, style: str = "minimalist", current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await EditorService.generate_cover(document_id, style, current_user),
        message="Khởi tạo ảnh bìa AI thành công."
    )
