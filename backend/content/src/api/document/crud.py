from typing import Any, List, Optional
from fastapi import APIRouter, Body, Depends, Header, Query
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

router = APIRouter()

@router.post("", response_model=APIResponse[Any], status_code=201)
async def create_document(
    doc_in: DocumentCreate,
    current_user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN])),
):
    return APIResponse(
        data=await DocumentService.create_document(doc_in, current_user),
        message="Khởi tạo tài liệu hoàn tất",
        status=201,
    )

@router.get("/ca-nhan", response_model=APIResponse[Any])
async def get_my_documents(
    q: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    data = await DocumentService.get_my_documents(
        current_user,
        q=q,
        cursor=cursor,
        limit=limit,
    )
    return APIResponse(data=data, message="Truy xuất danh sách tài liệu cá nhân hoàn tất")

@router.get(
    "/thung-rac",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def get_trash(current_user=Depends(get_current_user)):
    data = await DocumentService.get_trash(current_user)
    return APIResponse(data=data, message="Truy xuất thùng rác hoàn tất")


@router.get("", response_model=APIResponse[List[DocumentResponse]])
async def list_documents(
    limit: int = Query(default=20, le=100),
    cursor: Optional[str] = None,
    q: Optional[str] = None,
    sort_by: str = "latest",
    category: Optional[str] = None,
    tag: Optional[str] = None,
):
    return APIResponse(
        data=await DocumentService.list_documents(
            limit, cursor, q, sort_by, category, tag
        ),
        message="Trích xuất danh mục tài liệu hoàn tất",
    )

@router.post(
    "/{document_id}/khoi-phuc",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def restore_document(document_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.restore_document(document_id, current_user),
        message="Khôi phục tài liệu hoàn tất",
    )

@router.get("/tai-lieu/{slug}", response_model=APIResponse[Any])
async def get_document_by_slug(slug: str, current_user=Depends(get_current_user_optional)):
    return APIResponse(
        data=await DocumentService.get_document_by_slug(slug, current_user),
        message="Truy xuất tài liệu hoàn tất",
    )

@router.get("/xem-truoc/{slug}", response_model=APIResponse[Any])
async def get_document_preview(slug: str):
    return APIResponse(
        data=await DocumentService.get_document_preview(slug),
        message="Truy xuất bản xem trước tài liệu hoàn tất",
    )

@router.get("/{document_id}", response_model=APIResponse[Any])
async def get_document(
    document_id: str,
    password: Optional[str] = Header(None, alias="x-document-password"),
    current_user=Depends(get_current_user_optional),
):
    return APIResponse(
        data=await DocumentService.get_document_by_id(document_id, current_user, password=password),
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

@router.put("/{document_id}", response_model=APIResponse[Any])
async def update_document(
    document_id: str,
    doc_update: DocumentUpdate,
    current_user=Depends(get_current_user),
):
    return APIResponse(
        data=await DocumentService.update_document(document_id, doc_update, current_user),
        message="Cập nhật thông tin tài liệu hoàn tất",
    )

@router.delete(
    "/{document_id}",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def delete_document(document_id: str, current_user=Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.soft_delete_document(document_id, current_user),
        message="Chuyển tài liệu vào thùng rác hoàn tất",
    )

@router.post(
    "/{document_id}/bao-ve",
    response_model=APIResponse[Any],
    dependencies=[Depends(require_role([Role.AUTHOR, Role.ADMIN]))],
)
async def set_document_password(
    document_id: str,
    body: DocumentPasswordRequest,
    current_user=Depends(get_current_user),
):
    return APIResponse(
        data=await DocumentService.set_document_password(document_id, body.password, current_user),
        message="Cập nhật mật khẩu tài liệu hoàn tất",
    )

@router.post("/{document_id}/mo-khoa", response_model=APIResponse[Any])
async def unlock_document(
    document_id: str,
    password: str = Body(..., embed=True),
    current_user=Depends(get_current_user_optional),
):
    return APIResponse(
        data=await DocumentService.get_document_by_id(document_id, current_user, password),
        message="Xác thực quyền truy cập tài liệu hoàn tất",
    )
