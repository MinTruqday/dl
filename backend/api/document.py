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

@router.get("/tags-and-categories", response_model=APIResponse[Any])
async def get_tags_categories():
    return APIResponse(data=await DocumentService.get_tags_categories(), message="Lấy danh sách thẻ và danh mục thành công.", status=status.HTTP_200_OK)

@router.get("/trending", response_model=APIResponse[Any])
async def get_trending_documents(limit: int = 5):
    return APIResponse(data=await DocumentService.get_trending_documents(limit), message="Lấy danh sách tài liệu xu hướng thành công.", status=status.HTTP_200_OK)

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

@router.post("/{document_id}/publish", response_model=APIResponse[DocumentResponse])
async def publish_document(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return APIResponse(data=await DocumentService.publish_document(document_id, current_user), message="Xuất bản tài liệu thành công.", status=status.HTTP_200_OK)

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

@router.get("/semantic-search", response_model=APIResponse[Any])
async def semantic_search(query: str, limit: int = 10):
    return APIResponse(data=await DocumentService.get_semantic_search(query, limit), message="Tìm kiếm ngữ nghĩa thành công.", status=status.HTTP_200_OK)

@router.get("/{document_id}", response_model=APIResponse[DocumentResponse])
async def get_document_by_id(
    document_id: str,
    password: Optional[str] = Query(None),
    current_user: UserInDB = Depends(get_current_user_optional)
) -> Any:
    return APIResponse(data=await DocumentService.get_document_by_id(document_id, current_user, password), message="Lấy thông tin tài liệu thành công.", status=status.HTTP_200_OK)


@router.post("/{document_id}/compile", response_model=APIResponse[Any])
async def request_compilation(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return APIResponse(data=await DocumentService.request_compilation(document_id, current_user), message="Đã gửi yêu cầu biên dịch tài liệu.", status=status.HTTP_202_ACCEPTED)

@router.get("/slug/{slug}", response_model=APIResponse[DocumentResponse])
async def get_document_by_slug(
    slug: str,
    current_user: UserInDB = Depends(get_current_user_optional)
) -> Any:
    return APIResponse(data=await DocumentService.get_document_by_slug(slug, current_user), message="Lấy tài liệu theo đường dẫn thành công.", status=status.HTTP_200_OK)

@router.put("/{document_id}/cover", response_model=APIResponse[DocumentResponse])
async def update_cover(
    document_id: str,
    cover_url: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return APIResponse(data=await DocumentService.update_cover(document_id, cover_url, current_user), message="Cập nhật ảnh bìa thành công.", status=status.HTTP_200_OK)

class ChapterCreate(BaseModel):
    title: str
    content: str
    is_premium: bool = False
    price_dl: int = 0

class InviteCoauthorRequest(BaseModel):
    email: str

@router.post("/{document_id}/chapters", response_model=APIResponse[DocumentResponse])
async def add_chapter(
    document_id: str,
    chapter_in: ChapterCreate,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return APIResponse(data=await DocumentService.add_chapter(document_id, chapter_in, current_user), message="Thêm chương mới thành công.", status=status.HTTP_201_CREATED)

@router.post("/{document_id}/coauthors", response_model=APIResponse[Any])
async def invite_coauthor(
    document_id: str,
    req: InviteCoauthorRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return APIResponse(data=await DocumentService.invite_coauthor(document_id, req.email, current_user), message="Mời đồng tác giả thành công.", status=200)

@router.get("/{document_id}/export/epub", response_model=APIResponse[Any])
async def export_epub(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    content = await DocumentService.export_epub(document_id, current_user)
    headers = {"Content-Disposition": f'attachment; filename="DocLib_{document_id}.epub"'}
    return APIResponse(data=Response(content=content, media_type="application/epub+zip", headers=headers), message="Xuất bản sao EPUB thành công.", status=200)

@router.get("/{document_id}/qrcode", response_model=APIResponse[Any])
async def generate_qr_code(document_id: str):
    content = await DocumentService.generate_qr_code(document_id)
    return APIResponse(data=Response(content=content, media_type="image/png"), message="Tạo mã QR cho tài liệu thành công.", status=200)

@router.get("/{document_id}/chapters", response_model=APIResponse[Any])
async def get_document_chapters(document_id: str, current_user: UserInDB = Depends(get_current_user_optional)):
    return APIResponse(data=await DocumentService.get_document_chapters(document_id, current_user), message="Lấy danh sách chương thành công.", status=200)

@router.post("/{document_id}/ai-cover", response_model=APIResponse[Any])
async def generate_ai_cover(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.generate_ai_cover(document_id, current_user), message="Khởi tạo ảnh bìa AI thành công.", status=200)

@router.post("/{document_id}/warnings", response_model=APIResponse[Any])
async def set_warnings(document_id: str, warnings: List[str], current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.set_warnings(document_id, warnings, current_user), message="Thiết lập cảnh báo nội dung thành công.", status=200)

@router.post("/{document_id}/series", response_model=APIResponse[Any])
async def link_series(document_id: str, series_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.link_series(document_id, series_id, current_user), message="Liên kết chuỗi tài liệu thành công.", status=200)

@router.post("/{document_id}/custom-design", response_model=APIResponse[Any])
async def set_custom_design(document_id: str, custom_css: Optional[str] = None, custom_font: Optional[str] = None, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.set_custom_design(document_id, custom_css, custom_font, current_user), message="Cập nhật thiết kế tùy chỉnh thành công.", status=200)

@router.get("/recommendations/ai", response_model=APIResponse[Any])
async def get_ai_recommendations(limit: int = 10, current_user: UserInDB = Depends(get_current_user_optional)):
    return APIResponse(data=await DocumentService.get_ai_recommendations(limit), message="Lấy gợi ý tài liệu từ AI thành công.", status=200)

@router.get("/{document_id}/seo-meta", response_model=APIResponse[Any])
async def get_seo_meta(document_id: str):
    return APIResponse(data=await DocumentService.get_seo_meta(document_id), message="Lấy thông tin SEO tài liệu thành công.", status=200)

@router.get("/me/list", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def get_my_documents(skip: int = 0, limit: int = 50, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_my_documents(current_user, skip, limit),
        message="Lấy danh sách tài liệu cá nhân thành công."
    )

@router.get("/preview/{slug}", response_model=APIResponse[Any])
async def get_document_preview(slug: str):
    return APIResponse(
        data=await DocumentService.get_document_preview(slug),
        message="Lấy bản xem trước tài liệu thành công."
    )

@router.get("/{document_id}/analytics/dropoff", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def get_document_dropoff(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_document_dropoff(document_id, current_user),
        message="Lấy tỷ lệ rơi rớt độc giả thành công."
    )

class SchedulePublishRequest(BaseModel):
    publish_at: str

@router.post("/{document_id}/schedule", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def schedule_publish(document_id: str, req: SchedulePublishRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.schedule_publish(document_id, req.publish_at, current_user),
        message="Lên lịch xuất bản thành công."
    )

class FreePreviewRequest(BaseModel):
    chapter_ids: list

@router.post("/{document_id}/free-preview", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def set_free_preview(document_id: str, req: FreePreviewRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.set_free_preview(document_id, req.chapter_ids, current_user),
        message="Thiết lập chương đọc thử thành công."
    )

@router.delete("/{document_id}", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def soft_delete_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.soft_delete_document(document_id, current_user),
        message="Chuyển tài liệu vào thùng rác thành công."
    )

@router.post("/{document_id}/restore", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def restore_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.restore_document(document_id, current_user),
        message="Khôi phục tài liệu thành công."
    )

@router.get("/me/trash", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def get_trash(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.get_trash(current_user),
        message="Lấy danh sách thùng rác thành công."
    )

class DocumentPasswordRequest(BaseModel):
    password: str

@router.post("/{document_id}/password", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def set_document_password(document_id: str, req: DocumentPasswordRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.set_document_password(document_id, req.password, current_user),
        message="Thiết lập mật khẩu tài liệu thành công."
    )

class SeriesCreateRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    document_ids: list = []

@router.post("/series", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def create_series(req: SeriesCreateRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.create_series(req.model_dump(), current_user),
        message="Tạo chuỗi tài liệu thành công."
    )
