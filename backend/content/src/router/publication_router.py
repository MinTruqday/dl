from typing import Any, List, Optional

from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Body, Depends, status
from pydantic import BaseModel
from src.router.dependency_router import get_current_user, get_db, require_role
from src.schemas.document_schema import SchedulePublishRequest, SeoMetadataRequest
from src.services.document_service import DocumentService
from src.services.publication_service import PublicationService

router = APIRouter(prefix="/publications")


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
        message="The specified digital document has been successfully published and is now accessible to the designated audience",
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
        message="The automated publication schedule for the specified digital document has been successfully established",
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
        message="The search engine optimization metadata for the specified document has been successfully updated",
        status=200,
    )


@router.get("/{document_id}/readability", response_model=APIResponse[Any])
async def get_readability_score(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PublicationService.get_readability_score(
            document_id, current_user, db=db
        ),
        message="The automated linguistic readability analysis has been successfully completed for the specified document",
        status=200,
    )