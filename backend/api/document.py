from typing import Any
from core.response import APIResponse
from api.dependency import get_current_user_optional, get_current_user, require_role
from fastapi import APIRouter, Depends, Response, Query, status
from models.user import UserInDB, RoleEnum
from services.document import DocumentService
from models.document import DocumentCreate, DocumentResponse, DocumentContentUpdate
from typing import List, Any, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/documents")

@router.post("/", response_model=APIResponse[DocumentResponse])
async def create_document(
    doc_in: DocumentCreate,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return APIResponse(data=await DocumentService.create_document(doc_in, current_user), message="Tạo tài liệu mới thành công.", status=status.HTTP_201_CREATED)

@router.put("/{document_id}/content", response_model=APIResponse[DocumentResponse])
async def update_document_content(
    document_id: str,
    content_in: DocumentContentUpdate,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return APIResponse(data=await DocumentService.update_document_content(document_id, content_in, current_user), message="Cập nhật nội dung tài liệu thành công.", status=status.HTTP_200_OK)

@router.get("/", response_model=APIResponse[List[DocumentResponse]])
async def list_documents(
    limit: int = 10, 
    offset: int = 0,
    q: Optional[str] = None,
    sort_by: str = "latest",
    category: Optional[str] = None,
    tag: Optional[str] = None
) -> Any:
    return APIResponse(data=await DocumentService.list_documents(limit, offset, q, sort_by, category, tag), message="Lấy danh sách tài liệu thành công.", status=status.HTTP_200_OK)

@router.get("/me", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_my_documents(skip: int = 0, limit: int = 50, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_my_documents(current_user, skip, limit),
        message="Lấy danh sách tài liệu cá nhân thành công."
    )

@router.get("/me/trash", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_trash(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_trash(current_user),
        message="Lấy danh sách thùng rác thành công."
    )

@router.get("/{document_id}", response_model=APIResponse[DocumentResponse])
async def get_document_by_id(
    document_id: str,
    password: Optional[str] = Query(None),
    current_user: UserInDB = Depends(get_current_user_optional)
) -> Any:
    return APIResponse(data=await DocumentService.get_document_by_id(document_id, current_user, password), message="Lấy thông tin tài liệu thành công.", status=status.HTTP_200_OK)

@router.get("/slug/{slug}", response_model=APIResponse[DocumentResponse])
async def get_document_by_slug(
    slug: str,
    current_user: UserInDB = Depends(get_current_user_optional)
) -> Any:
    return APIResponse(data=await DocumentService.get_document_by_slug(slug, current_user), message="Lấy tài liệu theo đường dẫn thành công.", status=status.HTTP_200_OK)

@router.get("/{document_id}/chapters", response_model=APIResponse[Any])
async def get_document_chapters(document_id: str, current_user: UserInDB = Depends(get_current_user_optional)):
    return APIResponse(data=await DocumentService.get_document_chapters(document_id, current_user), message="Lấy danh sách chương thành công.", status=200)

@router.get("/preview/{slug}", response_model=APIResponse[Any])
async def get_document_preview(slug: str):
    return APIResponse(
        data=await DocumentService.get_document_preview(slug),
        message="Lấy bản xem trước tài liệu thành công."
    )

class SeriesCreateRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    document_ids: list = []

class InviteCoauthorRequest(BaseModel):
    email: str

class DocumentPasswordRequest(BaseModel):
    password: str


@router.get("/series/me", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_my_series(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_my_series(current_user),
        message="Lấy danh sách chuỗi tài liệu thành công."
    )

@router.get("/series/{series_id}", response_model=APIResponse[Any])
async def get_series_by_id(series_id: str):
    return APIResponse(
        data=await DocumentService.get_series_by_id(series_id),
        message="Lấy chi tiết chuỗi tài liệu thành công."
    )

@router.post("/series", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def create_series(req: SeriesCreateRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.create_series(req.model_dump(), current_user),
        message="Tạo chuỗi tài liệu thành công."
    )

@router.post("/{document_id}/link-series", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def link_series(document_id: str, series_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.link_series(document_id, series_id, current_user), 
        message="Liên kết chuỗi tài liệu thành công.", 
        status=200
    )

@router.post("/{document_id}/coauthors", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def invite_coauthor(document_id: str, req: InviteCoauthorRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.invite_coauthor(document_id, req.email, current_user), 
        message="Mời đồng tác giả thành công.", 
        status=200
    )

@router.delete("/{document_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def soft_delete_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.soft_delete_document(document_id, current_user),
        message="Chuyển tài liệu vào thùng rác thành công."
    )

@router.post("/{document_id}/restore", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def restore_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.restore_document(document_id, current_user),
        message="Khôi phục tài liệu thành công."
    )

@router.post("/{document_id}/password", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def set_document_password(document_id: str, req: DocumentPasswordRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.set_document_password(document_id, req.password, current_user),
        message="Thiết lập mật khẩu tài liệu thành công."
    )

@router.get("/{document_id}/analytics/dropoff", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_document_dropoff(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_document_dropoff(document_id, current_user),
        message="Lấy tỷ lệ rơi rớt độc giả thành công."
    )
@router.get("/{document_id}/audit-logs/", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_document_audit_logs(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    # Placeholder logic to retrieve document-specific audit logs
    return APIResponse(
        data=[], 
        message="Lấy nhật ký hoạt động tài liệu thành công."
    )
