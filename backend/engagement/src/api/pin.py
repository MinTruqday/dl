from typing import Any
from fastapi import APIRouter, Depends
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.api.dependency import get_current_user, get_db, CurrentUser
from src.schemas.pin import PinnedDocumentRequest
from src.services.pin import PinService

router = APIRouter(route_class=LoggingRoute, prefix="/ghim")

@router.get("", response_model=APIResponse[Any])
async def get_pinned_documents(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await PinService.get_pinned_documents(current_user),
        message="Trích xuất danh sách tài liệu ghim hoàn tất",
    )

@router.post("/{document_id}", response_model=APIResponse[Any])
async def pin_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PinService.pin_document(document_id, current_user),
        message="Thêm tài liệu vào danh sách ghim hoàn tất",
    )

@router.delete("/{document_id}", response_model=APIResponse[Any])
async def unpin_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PinService.unpin_document(document_id, current_user),
        message="Xóa tài liệu khỏi danh sách ghim hoàn tất",
    )

@router.put("", response_model=APIResponse[Any])
async def set_pinned_documents(
    data: PinnedDocumentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PinService.set_pinned_documents(
            data.document_ids, current_user
        ),
        message="Cập nhật sắp xếp tài liệu ghim hoàn tất",
    )
