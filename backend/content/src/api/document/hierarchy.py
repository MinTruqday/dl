from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from src.core.response import APIResponse
from src.api.dependency import get_current_user
from src.schemas.document import FolderCreate
from src.services.document import DocumentService

router = APIRouter()

@router.get("/thu-muc", response_model=APIResponse[Any])
async def get_folders(parent_id: Optional[str] = None, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_folders(parent_id, current_user),
        message="Truy xuất danh sách thư mục hoàn tất",
    )

@router.post("/thu-muc", response_model=APIResponse[Any])
async def create_folder(folder_in: FolderCreate, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.create_folder(folder_in.name, folder_in.parent_id, current_user),
        message="Tạo thư mục làm việc hoàn tất",
        status=201,
    )

@router.delete("/thu-muc/{folder_id}", response_model=APIResponse[Any])
async def delete_folder(folder_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.delete_folder(folder_id, current_user),
        message="Xóa thư mục làm việc hoàn tất",
    )

@router.post("/{document_id}/di-chuyen", response_model=APIResponse[Any])
async def move_document_to_folder(document_id: str, req: dict, current_user=Depends(get_current_user)):
    folder_id = req.get("folder_id")
    return APIResponse(
        data=await DocumentService.move_document_to_folder(document_id, folder_id, current_user),
        message="Di chuyển tài liệu hoàn tất",
    )

@router.post("/{document_id}/chuyen-nhuong", response_model=APIResponse[Any])
async def transfer_document(document_id: str, req: dict, current_user=Depends(get_current_user)):
    new_owner_id = req.get("new_owner_id", "")
    return APIResponse(
        data=await DocumentService.transfer_document(document_id, new_owner_id, current_user),
        message="Chuyển nhượng quyền sở hữu hoàn tất",
    )
