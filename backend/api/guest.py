from fastapi import APIRouter, Query
from pydantic import BaseModel, EmailStr
from services.guest import GuestService
from services.document import DocumentService
from services.admin import AdminService

router = APIRouter(prefix="/guest")

class NewsletterSubscribeRequest(BaseModel):
    email: EmailStr

@router.get("/documents/{document_id}/preview")
async def get_document_preview(document_id: str):
    return await DocumentService.get_document_preview(document_id)

@router.get("/authors/featured")
async def get_featured_authors(limit: int = Query(10, ge=1, le=50)):
    return await GuestService.get_featured_authors(limit)

@router.get("/authors/{author_slug}")
async def get_author_public_profile(author_slug: str):
    return await GuestService.get_author_public_profile(author_slug)

@router.post("/newsletter/subscribe")
async def subscribe_newsletter(req: NewsletterSubscribeRequest):
    return await GuestService.subscribe_newsletter(req.email)

@router.get("/system-notices")
async def get_system_notices():
    return await GuestService.get_system_notices()

@router.get("/banners")
async def get_banners():
    return await AdminService.get_banners(active_only=True)
