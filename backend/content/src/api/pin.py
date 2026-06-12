from typing import Any, List
from fastapi import APIRouter, Depends, Query
from src.api.dependency import get_db, get_current_user
from src.schemas.user import UserInDB
from src.schemas.library import PinnedDocumentRequest
from core.response import APIResponse
from src.services.pin import PinService
router = APIRouter(prefix='/ghim', tags=['Pin'])

@router.get('', response_model=APIResponse[Any])
async def get_pinned_documents(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PinService.get_pinned_documents(current_user, db=db), message='Lấy danh sách ghim success')

@router.post('/{document_id}', response_model=APIResponse[Any])
async def pin_document(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PinService.pin_document(document_id, current_user, db=db), message='Ghim tài liệu success')

@router.delete('/{document_id}', response_model=APIResponse[Any])
async def unpin_document(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PinService.unpin_document(document_id, current_user, db=db), message='Bỏ ghim tài liệu success')

@router.put('', response_model=APIResponse[Any])
async def set_pinned_documents(data: PinnedDocumentRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PinService.set_pinned_documents(data.document_ids, current_user, db=db), message='Cập nhật danh sách ghim success')