from typing import Any

from fastapi import APIRouter, Depends, Query
from src.api.dependency import get_current_user, get_db, require_role
from src.schemas.document import ModerateDocumentRequest
from src.services.document import DocumentService

from shared.infrastructure.configuration import settings
from shared.response import APIResponse
from shared.dependency import CurrentUser, Role

router = APIRouter(prefix="/ban-nhap")


@router.get(
    "/hang-doi",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.ADMIN]))],
)
async def get_approval_queue(
    cursor: str = None,
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_approval_queue(cursor, limit, db=db),
        message="Lấy danh sách tài liệu chờ duyệt thành công",
    )


@router.post(
    "/{document_id}/kiem-duyet",
    response_model=APIResponse[Any],
    dependency=[Depends(require_role([Role.ADMIN]))],
)
async def moderate_document(
    document_id: str,
    req: ModerateDocumentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.moderate_document(
            document_id, req.action, req.reason, current_user
        ),
        message="Cập nhật kiểm duyệt tài liệu thành công",
    )
