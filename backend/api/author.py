from typing import Any, List, Optional
from fastapi import APIRouter, Depends, status
from models.user import UserInDB, RoleEnum
from api.dependency import get_current_user, require_role
from core.response import APIResponse
from services.document import DocumentService
from pydantic import BaseModel

router = APIRouter(prefix="/authors")

class SeriesCreateRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    document_ids: list = []

class InviteCoauthorRequest(BaseModel):
    email: str

class DocumentPasswordRequest(BaseModel):
    password: str

@router.get("/me/documents", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def get_my_documents(skip: int = 0, limit: int = 50, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_my_documents(current_user, skip, limit),
        message="Lấy danh sách tài liệu cá nhân thành công."
    )

@router.get("/me/trash", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def get_trash(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_trash(current_user),
        message="Lấy danh sách thùng rác thành công."
    )

@router.post("/series", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def create_series(req: SeriesCreateRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.create_series(req.model_dump(), current_user),
        message="Tạo chuỗi tài liệu thành công."
    )

@router.post("/documents/{document_id}/link-series", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def link_series(document_id: str, series_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.link_series(document_id, series_id, current_user), 
        message="Liên kết chuỗi tài liệu thành công.", 
        status=200
    )

@router.post("/documents/{document_id}/coauthors", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def invite_coauthor(document_id: str, req: InviteCoauthorRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.invite_coauthor(document_id, req.email, current_user), 
        message="Mời đồng tác giả thành công.", 
        status=200
    )

@router.delete("/documents/{document_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def soft_delete_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.soft_delete_document(document_id, current_user),
        message="Chuyển tài liệu vào thùng rác thành công."
    )

@router.post("/documents/{document_id}/restore", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def restore_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.restore_document(document_id, current_user),
        message="Khôi phục tài liệu thành công."
    )

@router.post("/documents/{document_id}/password", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def set_document_password(document_id: str, req: DocumentPasswordRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.set_document_password(document_id, req.password, current_user),
        message="Thiết lập mật khẩu tài liệu thành công."
    )

@router.get("/analytics/dropoff/{document_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def get_document_dropoff(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_document_dropoff(document_id, current_user),
        message="Lấy tỷ lệ rơi rớt độc giả thành công."
    )
