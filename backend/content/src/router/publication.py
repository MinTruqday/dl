from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, status
from core.dependency import get_current_user, get_db, require_role
from src.schemas.documents import SchedulePublishRequest, SeoMetadataRequest
from src.services.publication import PublicationService

router = APIRouter(prefix="/xuat-cam-quyen")

@router.post("/{document_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author", "admin"]))])
async def publish_document(document_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PublicationService.publish_document(document_id, current_user, db=db),
        message="Lỗi khi truy xuất tài liệu",
        status=status.HTTP_200_OK,
    )

@router.post("/{document_id}/lich-trinh", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author"]))])
async def schedule_publish(document_id: str, req: SchedulePublishRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PublicationService.schedule_publish(document_id, req.publish_at, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
        status=200,
    )

@router.put("/{document_id}/tim-kiem", response_model=APIResponse[Any], dependencies=[Depends(require_role(["author"]))])
async def update_seo_metadata(document_id: str, req: SeoMetadataRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PublicationService.update_seo_metadata(document_id, req.model_dump(), current_user, db=db),
        message="Lỗi truy xuất cơ sở dữ liệu hệ thống",
        status=200,
    )

@router.get("/{document_id}/de-doc-hieu", response_model=APIResponse[Any])
async def get_readability_score(document_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PublicationService.get_readability_score(document_id, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )