from typing import Any

from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends, Query
from src.router.dependency_router import get_current_user, get_db, require_role
from src.schemas.document_schema import ModerateDocumentRequest
from src.services.document_service import DocumentService
from core.config import settings

router = APIRouter(prefix="/ban-nhap")


@router.get(
    "/hang-doi",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def get_approval_queue(
    cursor: str = None,
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_approval_queue(cursor, limit, db=db),
        message="Đã tải danh sách chờ phê duyệt",
    )


@router.post(
    "/{document_id}/kiem-duyet",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))],
)
async def moderate_document(
    document_id: str,
    req: ModerateDocumentRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.moderate_document(
            document_id, req.action, req.reason, current_user, db=db
        ),
        message="Đã xử lý tài liệu",
    )
