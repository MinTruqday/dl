from typing import Any, List

from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends, Query
from src.router.dependency_router import get_current_user, get_db
from src.schemas.library_schema import PinnedDocumentRequest
from src.services.pin_service import PinService

router = APIRouter(prefix="/pins")


@router.get("", response_model=APIResponse[Any])
async def get_pinned_documents(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await PinService.get_pinned_documents(current_user, db=db),
        message="The list of your prioritized pinned documents has been successfully retrieved",
    )


@router.post("/{document_id}", response_model=APIResponse[Any])
async def pin_document(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PinService.pin_document(document_id, current_user, db=db),
        message="The specified document has been successfully prioritized and added to your pinned list",
    )


@router.delete("/{document_id}", response_model=APIResponse[Any])
async def unpin_document(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PinService.unpin_document(document_id, current_user, db=db),
        message="The specified document has been successfully removed from your prioritized pinned list",
    )


@router.put("", response_model=APIResponse[Any])
async def set_pinned_documents(
    data: PinnedDocumentRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PinService.set_pinned_documents(
            data.document_ids, current_user, db=db
        ),
        message="The arrangement of your prioritized pinned documents has been successfully updated",
    )