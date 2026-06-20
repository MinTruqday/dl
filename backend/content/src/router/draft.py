from typing import Any

from fastapi import APIRouter, Depends, Query
from src.router.dependency import get_current_user, get_db, require_role
from src.schemas.document import ModerateDocumentRequest
from src.services.document import DocumentManager

from core.config import settings
from core.response import APIResponse
from core.schemas.user import RoleEnum, UserInDB

router = APIRouter(prefix="/ban-nhap")


@router.get(
    "/queue",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def get_approval_queue(
    cursor: str = None,
    limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentManager.get_approval_queue(cursor, limit, db=db),
        message="Lấy danh sách tài liệu chờ duyệt thành công",
    )


@router.post(
    "/{document_id}/moderate",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))],
)
async def moderate_document(
    document_id: str,
    req: ModerateDocumentRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await DocumentManager.moderate_document(
            document_id, req.action, req.reason, current_user, db=db
        ),
        message="Cập nhật kiểm duyệt tài liệu thành công",
    )
