from typing import Any
from core.config import settings
from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends, Query
from src.dependencies import get_current_user, get_db, require_role
from src.schemas.documents import ModerateDocumentRequest
from src.services.documents import DocumentService

router = APIRouter(prefix="/drafts")

@router.get("/queue", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def get_approval_queue(cursor: str = None, limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_approval_queue(cursor, limit, db=db),
        message="List of documents currently pending active administrative approval successfully retrieved internally",
    )

@router.post("/{document_id}/moderate", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])
async def moderate_document(document_id: str, req: ModerateDocumentRequest, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.moderate_document(document_id, req.action, req.reason, current_user, db=db),
        message="Administrative moderation resolution explicitly verified and permanently applied to specified document",
    )