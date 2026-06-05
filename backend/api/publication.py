from typing import Any, List, Optional
from core.response import APIResponse
from fastapi import APIRouter, Body, Depends, status
from models.user import UserInDB, RoleEnum
from api.dependency import get_current_user, require_role
from services.publication import PublicationService
from services.document import DocumentService
from services.chapter import ChapterService
from models.document import SchedulePublishRequest, PremiumConfigRequest, SeoMetadataRequest
from pydantic import BaseModel
router = APIRouter(prefix='/xuat-ban')

@router.post('/{document_id}', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def publish_document(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PublicationService.publish_document(document_id, current_user, db=db), message='Xuất bản tài liệu thành công', status=status.HTTP_200_OK)

@router.post('/{document_id}/len-lich', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def schedule_publish(document_id: str, req: SchedulePublishRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PublicationService.schedule_publish(document_id, req.publish_at, current_user, db=db), message='Lên lịch xuất bản tài liệu thành công', status=200)

@router.post('/{document_id}/tinh-phi', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def config_premium(document_id: str, req: PremiumConfigRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PublicationService.config_premium(document_id, req.premium_chapters, current_user, db=db), message='Thiết lập chương tính phí thành công', status=200)

@router.post('/{document_id}/doc-thu', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def set_free_preview(document_id: str, chapter_ids: List[str]=Body(...), current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await ChapterService.set_free_preview(document_id, chapter_ids, current_user, db=db), message='Thiết lập chương đọc thử thành công', status=200)

@router.put('/{document_id}/seo', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def update_seo_metadata(document_id: str, req: SeoMetadataRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PublicationService.update_seo_metadata(document_id, req.model_dump(), current_user, db=db), message='Cập nhật thông tin SEO tài liệu thành công', status=200)

@router.get('/{document_id}/doc-hieu', response_model=APIResponse[Any])
async def get_readability_score(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PublicationService.get_readability_score(document_id, current_user, db=db), message='Tính toán điểm độ đọc hiểu thành công', status=200)