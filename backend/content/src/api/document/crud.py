from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, UploadFile, File, Response
from src.core.logging_route import LoggingRoute
from src.core.response import APIResponse
from src.api.dependency import get_current_user, get_current_user_optional, require_role, CurrentUser, Role
from src.schemas.document import (
    DocumentContentUpdate,
    DocumentCreate,
    DocumentPasswordRequest,
    DocumentResponse,
    DocumentUpdate,
)
from src.services.document import DocumentService

router = APIRouter(route_class=LoggingRoute)

@router.post("", response_model=APIResponse[Any])
async def create_document(doc_in: DocumentCreate, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.create_document(doc_in, current_user),
        message="Khởi tạo tài liệu hoàn tất",
        status=201,
    )

@router.post("/nhap-file", response_model=APIResponse[Any])
async def import_document(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    try:
        data = await DocumentService.import_document_from_file(file, current_user)
        return APIResponse(data=data, message="Nhập tài liệu hoàn tất", status=201)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cua-toi", response_model=APIResponse[Any])
async def get_my_documents(
    status: Optional[str] = None,
    sort_by: str = "updated_at",
    limit: int = 50,
    cursor: Optional[str] = None,
    folder_id: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    data = await DocumentService.get_my_documents(
        current_user,
        status_filter=status,
        sort_by=sort_by,
        limit=limit,
        cursor=cursor,
        folder_id=folder_id,
    )
    return APIResponse(data=data, message="Truy xuất danh sách tài liệu cá nhân hoàn tất")

@router.get("/thung-rac", response_model=APIResponse[Any])
async def get_trash(current_user=Depends(get_current_user)):
    data = await DocumentService.get_trash(current_user)
    return APIResponse(data=data, message="Truy xuất thùng rác hoàn tất")

@router.post("/thung-rac/{document_id}/khoi-phuc", response_model=APIResponse[Any])
async def restore_document(document_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.restore_document(document_id, current_user),
        message="Khôi phục tài liệu hoàn tất",
    )

@router.get("/slug/{slug}", response_model=APIResponse[Any])
async def get_document_by_slug(slug: str, current_user=Depends(get_current_user_optional)):
    return APIResponse(
        data=await DocumentService.get_document_by_slug(slug, current_user),
        message="Truy xuất tài liệu hoàn tất",
    )

@router.get("/slug/{slug}/xem-truoc", response_model=APIResponse[Any])
async def get_document_preview(slug: str):
    return APIResponse(
        data=await DocumentService.get_document_preview(slug),
        message="Truy xuất bản xem trước tài liệu hoàn tất",
    )

@router.get("/{document_id}", response_model=APIResponse[Any])
async def get_document(
    document_id: str,
    password: Optional[str] = None,
    x_share_token: Optional[str] = Header(None, alias="X-Share-Token"),
    current_user=Depends(get_current_user_optional),
):
    return APIResponse(
        data=await DocumentService.get_document_by_id(
            document_id, current_user, password=password, share_token=x_share_token
        ),
        message="Truy xuất tài liệu hoàn tất",
    )

@router.put("/{document_id}/noi-dung", response_model=APIResponse[Any])
async def update_document_content(
    document_id: str,
    update_data: DocumentContentUpdate,
    current_user=Depends(get_current_user),
):
    return APIResponse(
        data=await DocumentService.update_document_content(document_id, update_data, current_user),
        message="Cập nhật nội dung tài liệu hoàn tất",
    )

@router.patch("/{document_id}", response_model=APIResponse[Any])
async def update_document(
    document_id: str,
    doc_update: DocumentUpdate,
    current_user=Depends(get_current_user),
):
    return APIResponse(
        data=await DocumentService.update_document(document_id, doc_update, current_user),
        message="Cập nhật thông tin tài liệu hoàn tất",
    )

@router.delete("/{document_id}", response_model=APIResponse[Any])
async def delete_document(document_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.soft_delete_document(document_id, current_user),
        message="Chuyển tài liệu vào thùng rác hoàn tất",
    )

@router.post("/{document_id}/mat-khau", response_model=APIResponse[Any])
async def set_document_password(
    document_id: str,
    body: DocumentPasswordRequest,
    current_user=Depends(get_current_user),
):
    return APIResponse(
        data=await DocumentService.set_document_password(document_id, body.password, current_user),
        message="Cập nhật mật khẩu tài liệu hoàn tất",
    )

@router.get("/{document_id}/khoa-giai-ma", response_model=APIResponse[Any])
async def get_decryption_key(document_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_document_decryption_key(document_id, current_user),
        message="Lấy khóa giải mã thành công",
    )
