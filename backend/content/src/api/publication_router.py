from typing import Any, List, Optional

from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Body, Depends, status
from pydantic import BaseModel
from src.api.dependency_router import get_current_user, get_db, require_role
from src.schemas.document_schema import (SchedulePublishRequest,
                                         SeoMetadataRequest)
from src.services.document_service import DocumentService
from src.services.publication_service import PublicationService

router = APIRouter(prefix="/publication")


@router.post(
    "/{document_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))],
)
async def publish_document(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PublicationService.publish_document(
            document_id, current_user, db=db
        ),
        message="Đã xuất bản tài liệu",
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
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PublicationService.schedule_publish(
            document_id, req.publish_at, current_user, db=db
        ),
        message="Đã lên lịch xuất bản",
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
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PublicationService.update_seo_metadata(
            document_id, req.model_dump(), current_user, db=db
        ),
        message="Đã cập nhật thông tin SEO",
        status=200,
    )


@router.get("/{document_id}/doc-hieu", response_model=APIResponse[Any])
async def get_readability_score(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PublicationService.get_readability_score(
            document_id, current_user, db=db
        ),
        message="Đã tính điểm đọc hiểu",
        status=200,
    )
