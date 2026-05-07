from typing import Any, List, Optional
from core.response import APIResponse
from fastapi import APIRouter, Depends, status
from models.user import UserInDB, RoleEnum
from api.dependency import get_current_user, require_role
from services.publish import PublisherService
from services.document import DocumentService
from services.chapter import ChapterService
from pydantic import BaseModel

router = APIRouter(prefix="/publish")

class SchedulePublishRequest(BaseModel):
    publish_at: str

class PremiumConfigRequest(BaseModel):
    premium_chapters: List[str]

class SeoMetadataRequest(BaseModel):
    tags: List[str] = []
    keywords: List[str] = []
    slug: str = ""
    description: str = ""

@router.post("/{document_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def publish_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await PublisherService.publish_document(document_id, current_user), 
        message="Xuất bản tài liệu thành công.", 
        status=status.HTTP_200_OK
    )

@router.post("/{document_id}/schedule", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def schedule_publish(document_id: str, req: SchedulePublishRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await PublisherService.schedule_publish(document_id, req.publish_at, current_user), 
        message="Lên lịch xuất bản tài liệu thành công.", 
        status=200
    )

@router.post("/{document_id}/premium", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def config_premium(document_id: str, req: PremiumConfigRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        # Note: both config_premium and set_free_preview are related to monetization
        # config_premium is currently in PublisherService, let's keep it there for now
        data=await PublisherService.config_premium(document_id, req.premium_chapters, current_user), 
        message="Thiết lập chương tính phí thành công.", 
        status=200
    )

@router.post("/{document_id}/free-preview", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def set_free_preview(document_id: str, chapter_ids: List[str], current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ChapterService.set_free_preview(document_id, chapter_ids, current_user), 
        message="Thiết lập chương đọc thử thành công.", 
        status=200
    )

@router.put("/{document_id}/seo", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def update_seo_metadata(document_id: str, req: SeoMetadataRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await PublisherService.update_seo_metadata(document_id, req.model_dump(), current_user), 
        message="Cập nhật thông tin SEO tài liệu thành công.", 
        status=200
    )

@router.get("/{document_id}/readability", response_model=APIResponse[Any])
async def get_readability_score(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await PublisherService.get_readability_score(document_id, current_user), 
        message="Tính toán điểm độ đọc hiểu thành công.", 
        status=200
    )
