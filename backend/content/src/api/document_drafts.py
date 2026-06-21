from typing import Any

from fastapi import APIRouter, Depends, Query
from src.api.system_dependency import get_current_user, get_db, require_role
from src.schemas.document_metadata import ModerateDocumentRequest
from src.services.document import DocumentMetadata

from core.config import settings
from core.response import APIResponse
from core.dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/ban-nhap")


@router.get(
    "/hang-doi",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_approval_queue(
    cursor: str = None,
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentMetadata.get_approval_queue(cursor, limit, db=db),
        message="Lấy danh sách tài liệu chờ duyệt thành công",
    )


@router.post(
    "/{document_id}/kiem-duyet",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def moderate_document(
    document_id: str,
    req: ModerateDocumentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentMetadata.moderate_document(
            document_id, req.action, req.reason, current_user, db=db
        ),
        message="Cập nhật kiểm duyệt tài liệu thành công",
    )
