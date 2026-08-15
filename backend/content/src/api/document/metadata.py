from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.api.dependency import get_current_user, require_role, Role
from src.services.document import DocumentService

router = APIRouter(route_class=LoggingRoute)

@router.get("/{document_id}/thong-ke", response_model=APIResponse[Any])
async def get_document_analytics(document_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_document_analytics(document_id, current_user),
        message="Truy xuất dữ liệu phân tích tài liệu hoàn tất",
    )

@router.get("/{document_id}/chi-so-hoc-thuat", response_model=APIResponse[Any])
async def get_document_academic(document_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_document_academic(document_id, current_user),
        message="Truy xuất chỉ số học thuật hoàn tất",
    )

@router.get(
    "/hang-doi-duyet",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.ADMIN]))],
)
async def get_approval_queue(cursor: Optional[str] = None, limit: int = 50):
    return APIResponse(
        data=await DocumentService.get_approval_queue(cursor=cursor, limit=limit),
        message="Truy xuất hàng đợi duyệt tài liệu hoàn tất",
    )

@router.get("/thinh-hanh", response_model=APIResponse[List[dict]])
async def get_trending_documents(limit: int = Query(default=20, le=100)):
    return APIResponse(
        data=await DocumentService.get_trending_documents(limit=limit),
        message="Truy xuất danh sách tài liệu thịnh hành hoàn tất",
    )

@router.get("/goi-y", response_model=APIResponse[List[dict]])
async def get_suggested_documents(limit: int = Query(default=20, le=100)):
    return APIResponse(
        data=await DocumentService.get_suggested_documents(limit=limit),
        message="Truy xuất danh sách tài liệu gợi ý hoàn tất",
    )
