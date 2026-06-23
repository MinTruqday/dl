from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, status
from pydantic import BaseModel
from src.api.dependency import get_current_user, get_db, require_role
from src.schemas.metadata import SchedulePublishRequest, SeoMetadataRequest
from src.services.metadata import DocumentMetadata
from src.services.publication_workflows import PublicationProcess

from shared.responses import APIResponse
from shared.dependencies import CurrentUser, RoleEnum

router = APIRouter(prefix="/xuat-ban")


@router.post(
    "/{document_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def publish_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PublicationProcess.publish_document(
            document_id, current_user, db=db
        ),
        message="Tài liệu đã được xuất bản",
        status=status.HTTP_200_OK,
    )


@router.post(
    "/{document_id}/len-lich",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR]))],
)
async def schedule_publish(
    document_id: str,
    req: SchedulePublishRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PublicationProcess.schedule_publish(
            document_id, req.publish_at, current_user, db=db
        ),
        message="Lên lịch xuất bản tài liệu tự động thành công",
        status=200,
    )


@router.put(
    "/{document_id}/seo",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR]))],
)
async def update_seo_metadata(
    document_id: str,
    req: SeoMetadataRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PublicationProcess.update_seo_metadata(
            document_id, req.model_dump(), current_user, db=db
        ),
        message="Cập nhật dữ liệu chuẩn SEO thành công",
        status=200,
    )


@router.get("/{document_id}/do-de-doc", response_model=APIResponse[Any])
async def get_readability_score(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PublicationProcess.get_readability_score(
            document_id, current_user, db=db
        ),
        message="Phân tích khả năng đọc thành công",
        status=200,
    )
