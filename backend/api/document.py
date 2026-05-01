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

