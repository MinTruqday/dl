from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Query
from pydantic import BaseModel, EmailStr
from services.guest import GuestService
from services.document import DocumentService
from services.admin import AdminService

router = APIRouter(prefix="/guest")

class NewsletterSubscribeRequest(BaseModel):
    email: EmailStr

@router.get("/documents/{document_id}/preview", response_model=APIResponse[Any])
async def get_document_preview(document_id: str):
    return APIResponse(data=await DocumentService.get_document_preview(document_id), message="Lấy bản xem trước tài liệu thành công.", status=200)

@router.get("/authors/featured", response_model=APIResponse[Any])
async def get_featured_authors(limit: int = Query(10, ge=1, le=50)):
    return APIResponse(data=await GuestService.get_featured_authors(limit), message="Lấy danh sách tác giả nổi bật thành công.", status=200)

@router.get("/authors/{author_slug}", response_model=APIResponse[Any])
async def get_author_public_profile(author_slug: str):
    return APIResponse(data=await GuestService.get_author_public_profile(author_slug), message="Lấy thông tin tác giả thành công.", status=200)

@router.post("/newsletter/subscribe", response_model=APIResponse[Any])
async def subscribe_newsletter(req: NewsletterSubscribeRequest):
    return APIResponse(data=await GuestService.subscribe_newsletter(req.email), message="Đăng ký nhận bản tin thành công.", status=201)

@router.get("/system-notices", response_model=APIResponse[Any])
async def get_system_notices():
    return APIResponse(data=await GuestService.get_system_notices(), message="Lấy thông báo hệ thống thành công.", status=200)

@router.get("/banners", response_model=APIResponse[Any])
async def get_banners():
    return APIResponse(data=await AdminService.get_banners(active_only=True), message="Lấy danh sách banner quảng cáo thành công.", status=200)
