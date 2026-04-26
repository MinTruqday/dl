from fastapi import APIRouter, Depends
from models.user import UserInDB
from api.dependencies import get_current_user
from services.publisher import PublisherService

router = APIRouter()

@router.put("/documents/{document_id}/seo")
async def update_seo_metadata(document_id: str, seo_data: dict, current_user: UserInDB = Depends(get_current_user)):
    return await PublisherService.update_seo_metadata(document_id, seo_data, current_user)

@router.get("/documents/{document_id}/readability")
async def get_readability_score(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await PublisherService.get_readability_score(document_id, current_user)

@router.post("/documents/{document_id}/schedule")
async def schedule_publish(document_id: str, publish_at: str, current_user: UserInDB = Depends(get_current_user)):
    return await PublisherService.schedule_publish(document_id, publish_at, current_user)

@router.post("/premium/{document_id}")
async def config_premium(document_id: str, premium_chapters: list[str], current_user: UserInDB = Depends(get_current_user)):
    return await PublisherService.config_premium(document_id, premium_chapters, current_user)
