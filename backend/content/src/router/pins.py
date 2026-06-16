from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends
from core.dependency import get_current_user, get_db
from src.schemas.library import PinnedDocumentRequest
from src.services.pins import PinService

router = APIRouter(prefix="/ghim-trang")

@router.get("", response_model=APIResponse[Any])
async def get_pinned_documents(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PinService.get_pinned_documents(current_user, db=db),
        message="Lỗi khi truy xuất tài liệu",
    )

@router.post("/{document_id}", response_model=APIResponse[Any])
async def pin_document(document_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PinService.pin_document(document_id, current_user, db=db),
        message="Lỗi truy xuất cơ sở dữ liệu hệ thống",
    )

@router.delete("/{document_id}", response_model=APIResponse[Any])
async def unpin_document(document_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PinService.unpin_document(document_id, current_user, db=db),
        message="Lỗi truy xuất cơ sở dữ liệu hệ thống",
    )

@router.put("", response_model=APIResponse[Any])
async def set_pinned_documents(data: PinnedDocumentRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await PinService.set_pinned_documents(data.document_ids, current_user, db=db),
        message="Lỗi truy xuất cơ sở dữ liệu hệ thống",
    )