from typing import Any
from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends, status
from src.dependencies import get_current_user, get_db, require_role
from src.schemas.documents import SchedulePublishRequest, SeoMetadataRequest
from src.services.publication import PublicationService

router = APIRouter(prefix="/publications")

@router.post("/{document_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def publish_document(document_id: str, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PublicationService.publish_document(document_id, current_user, db=db),
        message="Specified digital document systematically processed navigating automated publication deployment functional workflow",
        status=status.HTTP_200_OK,
    )

@router.post("/{document_id}/schedule", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def schedule_publish(document_id: str, req: SchedulePublishRequest, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PublicationService.schedule_publish(document_id, req.publish_at, current_user, db=db),
        message="Automated chronological execution mapping specified public dissemination task decisively activated recorded",
        status=200,
    )

@router.put("/{document_id}/seo", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def update_seo_metadata(document_id: str, req: SeoMetadataRequest, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PublicationService.update_seo_metadata(document_id, req.model_dump(), current_user, db=db),
        message="Extracted systematic optimization routing analytical properties configuring structural index decisively customized",
        status=200,
    )

@router.get("/{document_id}/readability", response_model=APIResponse[Any])
async def get_readability_score(document_id: str, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PublicationService.get_readability_score(document_id, current_user, db=db),
        message="Advanced statistical linguistic assessment processing document readability logic properly finalized calculating",
        status=200,
    )