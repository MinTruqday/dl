from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends
from models.user import UserInDB
from api.dependencies import get_current_user
from services.publisher import PublisherService

router = APIRouter()

@router.put("/documents/{document_id}/seo", response_model=APIResponse[Any])
async def update_seo_metadata(document_id: str, seo_data: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PublisherService.update_seo_metadata(document_id, seo_data, current_user), message="Cập nhật thông tin SEO tài liệu thành công.", status=200)

@router.get("/documents/{document_id}/readability", response_model=APIResponse[Any])
async def get_readability_score(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PublisherService.get_readability_score(document_id, current_user), message="Tính toán điểm độ đọc hiểu thành công.", status=200)

@router.post("/documents/{document_id}/schedule", response_model=APIResponse[Any])
async def schedule_publish(document_id: str, publish_at: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PublisherService.schedule_publish(document_id, publish_at, current_user), message="Lên lịch xuất bản tài liệu thành công.", status=200)

@router.post("/premium/{document_id}", response_model=APIResponse[Any])
async def config_premium(document_id: str, premium_chapters: list[str], current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await PublisherService.config_premium(document_id, premium_chapters, current_user), message="Thiết lập chương Premium thành công.", status=200)
