from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Query
from src.api.dependency import get_current_user, get_db, require_role
from src.schemas.document import ModerateDocumentRequest
from src.services.document import DocumentService

from src.core.infrastructure.configuration import settings
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/ban-nhap")

@router.get(
    "/hang-doi",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_approval_queue(
    cursor: str = None,
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentService.get_approval_queue(cursor, limit),
        message="Lấy danh sách tài liệu chờ duyệt thành công",
    )

@router.post(
    "/{document_id}/kiem-duyet",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
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
