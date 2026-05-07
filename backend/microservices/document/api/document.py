from typing import Any, List, Optional
from core.response import APIResponse
from api.dependency import get_current_user_optional, get_current_user, require_role
from fastapi import APIRouter, Depends, Response, Query, status
from models.user import UserInDB, RoleEnum
from services.document import DocumentService
from services.series import SeriesService
from services.chapter import ChapterService
from models.document import DocumentCreate, DocumentResponse, DocumentContentUpdate
from pydantic import BaseModel
router = APIRouter(prefix="/tai-lieu")
@router.post("/", response_model=APIResponse[DocumentResponse])
async def create_document(
    doc_in: DocumentCreate,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return APIResponse(data=await DocumentService.create_document(doc_in, current_user), message="Tạo tài liệu mới thành công", status=status.HTTP_201_CREATED)
@router.put("/{document_id}/noi-dung", response_model=APIResponse[DocumentResponse])
async def update_document_content(
    document_id: str,
    content_in: DocumentContentUpdate,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return APIResponse(data=await DocumentService.update_document_content(document_id, content_in, current_user), message="Cập nhật nội dung tài liệu thành công", status=status.HTTP_200_OK)
@router.get("/", response_model=APIResponse[List[DocumentResponse]])
async def list_documents(
    limit: int = 10, 
    offset: int = 0,
    q: Optional[str] = None,
    sort_by: str = "latest",
    category: Optional[str] = None,
    tag: Optional[str] = None
) -> Any:
    return APIResponse(data=await DocumentService.list_documents(limit, offset, q, sort_by, category, tag), message="Lấy danh sách tài liệu thành công", status=status.HTTP_200_OK)
@router.get("/ca-nhan", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_my_documents(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_my_documents(current_user, skip, limit),
        message="Lấy danh sách tài liệu cá nhân thành công"
    )
@router.get("/thung-rac", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_trash(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_trash(current_user),
        message="Lấy danh sách thùng rác thành công"
    )
@router.get("/{document_id}", response_model=APIResponse[DocumentResponse])
async def get_document_by_id(
    document_id: str,
    password: Optional[str] = Query(None),
    current_user: UserInDB = Depends(get_current_user_optional)
) -> Any:
    return APIResponse(data=await DocumentService.get_document_by_id(document_id, current_user, password), message="Lấy thông tin tài liệu thành công", status=status.HTTP_200_OK)
@router.get("/d/{slug}", response_model=APIResponse[DocumentResponse])
async def get_document_by_slug(
    slug: str,
    current_user: UserInDB = Depends(get_current_user_optional)
) -> Any:
    return APIResponse(data=await DocumentService.get_document_by_slug(slug, current_user), message="Lấy tài liệu theo đường dẫn thành công", status=status.HTTP_200_OK)
@router.get("/{document_id}/chuong", response_model=APIResponse[Any])
async def get_document_chapters(document_id: str, current_user: UserInDB = Depends(get_current_user_optional)):
    return APIResponse(data=await ChapterService.get_document_chapters(document_id, current_user), message="Lấy danh sách chương thành công", status=200)
@router.get("/xem-truoc/{slug}", response_model=APIResponse[Any])
async def get_document_preview(slug: str):
    return APIResponse(
        data=await DocumentService.get_document_preview(slug),
        message="Lấy bản xem trước tài liệu thành công"
    )
class SeriesCreateRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    document_ids: List[str] = []
class InviteCoauthorRequest(BaseModel):
    email: str
class DocumentPasswordRequest(BaseModel):
    password: str
@router.get("/chuoi-tai-lieu/ca-nhan", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_my_series(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await SeriesService.get_my_series(current_user),
        message="Lấy danh sách chuỗi tài liệu thành công"
    )
@router.get("/chuoi-tai-lieu/{series_id}", response_model=APIResponse[Any])
async def get_series_by_id(series_id: str):
    return APIResponse(
        data=await SeriesService.get_series_by_id(series_id),
        message="Lấy chi tiết chuỗi tài liệu thành công"
    )
@router.post("/chuoi-tai-lieu", response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def create_series(req: SeriesCreateRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await SeriesService.create_series(req.model_dump(), current_user),
        message="Tạo chuỗi tài liệu thành công",
        status=status.HTTP_201_CREATED
    )
@router.put("/chuoi-tai-lieu/{series_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def update_series(series_id: str, req: SeriesCreateRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await SeriesService.update_series(series_id, req.model_dump(), current_user),
        message="Cập nhật chuỗi tài liệu thành công"
    )
@router.delete("/chuoi-tai-lieu/{series_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def delete_series(series_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await SeriesService.delete_series(series_id, current_user),
        message="Xóa chuỗi tài liệu thành công"
    )
@router.patch("/chuoi-tai-lieu/{series_id}/tai-lieu", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def reorder_series_documents(series_id: str, document_ids: List[str], current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await SeriesService.reorder_series_documents(series_id, document_ids, current_user),
        message="Sắp xếp lại thứ tự tài liệu thành công"
    )
@router.post("/{document_id}/chuoi-tai-lieu/{series_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def link_series(document_id: str, series_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await SeriesService.link_series(document_id, series_id, current_user), 
        message="Liên kết chuỗi tài liệu thành công", 
        status=200
    )
@router.post("/{document_id}/dong-tac-gia", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def invite_coauthor(document_id: str, req: InviteCoauthorRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.invite_coauthor(document_id, req.email, current_user), 
        message="Mời đồng tác giả thành công", 
        status=200
    )
@router.delete("/{document_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def soft_delete_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.soft_delete_document(document_id, current_user),
        message="Chuyển tài liệu vào thùng rác thành công"
    )
@router.post("/{document_id}/khoi-phuc", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def restore_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.restore_document(document_id, current_user),
        message="Khôi phục tài liệu thành công"
    )
@router.post("/{document_id}/bao-ve", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def set_document_password(document_id: str, req: DocumentPasswordRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.set_document_password(document_id, req.password, current_user),
        message="Thiết lập mật khẩu tài liệu thành công"
    )
@router.get("/{document_id}/phan-tich/roi-rot", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_document_dropoff(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ChapterService.get_document_dropoff(document_id, current_user),
        message="Lấy tỷ lệ rơi rớt độc giả thành công"
    )
@router.get("/{document_id}/nhat-ky-hoat-dong", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_document_audit_logs(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_document_audit_logs(document_id, current_user), 
        message="Lấy nhật ký hoạt động tài liệu thành công"
    )
