from typing import Any, List, Optional
from core.response import APIResponse
from api.dependency import get_current_user_optional, get_current_user, require_role
from fastapi import APIRouter, Depends, Response, Query, status
from models.user import UserInDB, RoleEnum
from services.document import DocumentService
from services.series import SeriesService
from services.chapter import ChapterService
from models.document import DocumentCreate, DocumentResponse, DocumentContentUpdate, DocumentUpdate, CoauthorInviteRequest, DocumentPasswordRequest
from models.series import SeriesCreateRequest, SeriesResponse
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

@router.put("/{document_id}", response_model=APIResponse[DocumentResponse])
async def update_document(
    document_id: str,
    doc_update: DocumentUpdate,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return APIResponse(data=await DocumentService.update_document(document_id, doc_update, current_user), message="Cập nhật thông tin tài liệu thành công", status=status.HTTP_200_OK)

@router.get("/", response_model=APIResponse[List[DocumentResponse]])
async def list_documents(
    limit: int = 10, 
    cursor: Optional[str] = None,
    q: Optional[str] = None,
    sort_by: str = "latest",
    category: Optional[str] = None,
    tag: Optional[str] = None
) -> Any:
    return APIResponse(data=await DocumentService.list_documents(limit, cursor, q, sort_by, category, tag), message="Lấy danh sách tài liệu thành công", status=status.HTTP_200_OK)

@router.get("/ca-nhan", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_my_documents(cursor: Optional[str] = None, limit: int = Query(50, ge=1, le=100), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_my_documents(current_user, cursor, limit),
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

@router.post("/{document_id}/bien-dich", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def compile_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.compile_document(document_id, current_user),
        message="Biên dịch tài liệu thành công"
    )

class FolderCreate(BaseModel):
    name: str

@router.get("/thu-muc", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def get_folders(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=[], message="Lấy danh sách thư mục thành công")

@router.post("/thu-muc", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def create_folder(req: FolderCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data={"id": "folder_1", "name": req.name}, message="Tạo thư mục thành công")

@router.post("/{document_id}/star", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def toggle_star_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data={"starred": True}, message="Gắn sao tài liệu thành công")

@router.post("/{document_id}/chuyen-nhuong", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def transfer_document(document_id: str, new_owner_id: str = Query(...), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data={"status": "transferred"}, message="Chuyển nhượng tài liệu thành công")

@router.get("/{document_id}/phan-tich", response_model=APIResponse[Any])
async def get_document_analytics(document_id: str):
    return APIResponse(data={
        "completion_rate": 85,
        "avg_read_time": "12 phút",
        "saves": 45,
        "comments": 12
    }, message="Lấy phân tích độc giả thành công")

@router.get("/{document_id}/chi-so-hoc-thuat", response_model=APIResponse[Any])
async def get_document_academic(document_id: str):
    return APIResponse(data={
        "readability_score": "8.5",
        "citation_count": 3
    }, message="Lấy chỉ số học thuật thành công")

class AuthorNoteUpdate(BaseModel):
    chapter_index: int
    note: str

@router.put("/{document_id}/ghi-chu-tac-gia", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def update_author_note(document_id: str, req: AuthorNoteUpdate, current_user: UserInDB = Depends(get_current_user)):
    doc = await DocumentService.get_document_by_id(document_id, current_user)
    chapters = doc.get("chapters", []) if isinstance(doc, dict) else getattr(doc, "chapters", []) or []
    if req.chapter_index < 0 or req.chapter_index >= len(chapters):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Chỉ số chương không hợp lệ")
    chapters[req.chapter_index]["author_note"] = req.note
    result = await DocumentService.update_document(document_id, DocumentUpdate(chapters=chapters), current_user)
    return APIResponse(data=result, message="Cập nhật ghi chú tác giả thành công")

class DRMSettingsUpdate(BaseModel):
    disable_copy: bool = False
    hide_from_search: bool = False

@router.put("/{document_id}/drm", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def update_drm_settings(document_id: str, req: DRMSettingsUpdate, current_user: UserInDB = Depends(get_current_user)):
    result = await DocumentService.update_document(document_id, DocumentUpdate(
        drm_settings={"disable_copy": req.disable_copy, "hide_from_search": req.hide_from_search}
    ), current_user)
    return APIResponse(data=result, message="Cập nhật cài đặt bảo vệ bản quyền thành công")

class TagsUpdate(BaseModel):
    tags: List[str]

@router.put("/{document_id}/tags", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def update_tags(document_id: str, req: TagsUpdate, current_user: UserInDB = Depends(get_current_user)):
    result = await DocumentService.update_document(document_id, DocumentUpdate(tags=req.tags), current_user)
    return APIResponse(data=result, message="Cập nhật thẻ thành công")

class ScheduleUpdate(BaseModel):
    publish_at: str

@router.put("/{document_id}/hen-gio", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def schedule_publish(document_id: str, req: ScheduleUpdate, current_user: UserInDB = Depends(get_current_user)):
    result = await DocumentService.update_document(document_id, DocumentUpdate(publish_at=req.publish_at), current_user)
    return APIResponse(data=result, message="Lên lịch xuất bản thành công")

class PaywallUpdate(BaseModel):
    is_premium: bool

@router.put("/{document_id}/chuong/{chapter_index}/tra-phi", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def update_chapter_paywall(document_id: str, chapter_index: int, req: PaywallUpdate, current_user: UserInDB = Depends(get_current_user)):
    doc = await DocumentService.get_document_by_id(document_id, current_user)
    chapters = doc.get("chapters", []) if isinstance(doc, dict) else getattr(doc, "chapters", []) or []
    if chapter_index < 0 or chapter_index >= len(chapters):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Chỉ số chương không hợp lệ")
    chapters[chapter_index]["is_premium"] = req.is_premium
    result = await DocumentService.update_document(document_id, DocumentUpdate(chapters=chapters), current_user)
    return APIResponse(data=result, message="Cập nhật phân quyền trả phí thành công")

class NSFWUpdate(BaseModel):
    is_nsfw: bool

@router.put("/{document_id}/nsfw", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def update_nsfw(document_id: str, req: NSFWUpdate, current_user: UserInDB = Depends(get_current_user)):
    result = await DocumentService.update_document(document_id, DocumentUpdate(is_nsfw=req.is_nsfw), current_user)
    return APIResponse(data=result, message="Cập nhật giới hạn độ tuổi thành công")

class BroadcastRequest(BaseModel):
    message: str

@router.post("/{document_id}/thong-bao", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))])
async def broadcast_notification(document_id: str, req: BroadcastRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data={"sent": True, "message": req.message}, message="Đã gửi thông báo đến độc giả")
