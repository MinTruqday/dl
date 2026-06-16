from typing import Any
from core.config import settings
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from core.dependency import get_current_user, get_db, require_role
from src.schemas.documents import ModerateDocumentRequest
from src.services.documents import DocumentService

router = APIRouter(prefix="/cam-quyen-nhap-lieu")

@router.get("/hang-doi", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def get_approval_queue(cursor: str = None, limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.get_approval_queue(cursor, limit, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.post("/{document_id}/kiem-duyet", response_model=APIResponse[Any], dependencies=[Depends(require_role(["admin"]))])
async def moderate_document(document_id: str, req: ModerateDocumentRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await DocumentService.moderate_document(document_id, req.action, req.reason, current_user, db=db),
        message="Lỗi khi truy xuất tài liệu",
    )