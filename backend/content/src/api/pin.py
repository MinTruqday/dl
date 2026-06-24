from typing import Any, List

from fastapi import APIRouter, Depends, Query
from src.api.dependency import get_current_user, get_db
from src.schemas.library import PinnedDocumentRequest
from src.services.pin import PinService

from shared.response import APIResponse
from shared.dependency import CurrentUser, Role

router = APIRouter(prefix="/ghim")


@router.get("", response_model=APIResponse[Any])
async def get_pinned_documents(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await PinService.get_pinned_documents(current_user, db=db),
        message="Lấy danh sách tài liệu ghim thành công",
    )


@router.post("/{document_id}", response_model=APIResponse[Any])
async def pin_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PinService.pin_document(document_id, current_user, db=db),
        message="Thêm tài liệu vào danh sách ghim thành công",
    )


@router.delete("/{document_id}", response_model=APIResponse[Any])
async def unpin_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PinService.unpin_document(document_id, current_user, db=db),
        message="Xóa tài liệu khỏi danh sách ghim thành công",
    )


@router.put("", response_model=APIResponse[Any])
async def set_pinned_documents(
    data: PinnedDocumentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await PinService.set_pinned_documents(
            data.document_ids, current_user, db=db
        ),
        message="Cập nhật sắp xếp tài liệu ghim thành công",
    )
