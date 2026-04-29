from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query, Body
from api.dependencies import get_current_user, require_role
from models.user import UserInDB, RoleEnum
from services.reader import ReaderService
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/reader")

class TypographyRequest(BaseModel):
    font_family: str
    font_size: int = 16
    line_height: float = 1.8
    letter_spacing: float = 0

class ExcerptShareRequest(BaseModel):
    document_id: str
    text: str
    caption: str = ""

class PrivacyRequest(BaseModel):
    hide_reading_activity: bool = False
    hide_library: bool = False

class ProgressUpdate(BaseModel):
    document_id: str
    progress_percentage: float
    current_chapter_slug: str = None

class RatingCreate(BaseModel):
    rating: int
    review_text: str = None

class ReadingListCreate(BaseModel):
    name: str
    description: str = None
    is_public: bool = True

class FlashcardGenerateRequest(BaseModel):
    text: str
    context: str

class BookmarkFolderCreate(BaseModel):
    name: str

class BookmarkFolderAssign(BaseModel):
    bookmark_ids: List[str]

class ChapterRatingCreate(BaseModel):
    chapter_slug: str
    rating: int

class TypoReportCreate(BaseModel):
    chapter_slug: str
    text_excerpt: str
    description: str = ""

class ReadingGoalCreate(BaseModel):
    target_documents: int = 0
    target_pages: int = 0
    period: str = "monthly"

class PinnedDocumentRequest(BaseModel):
    document_ids: List[str]

class SettingsUpdateRequest(BaseModel):
    settings: dict

@router.put("/settings/typography", response_model=APIResponse[Any])
async def update_typography(data: TypographyRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.update_typography(data.model_dump(), current_user), message="Cập nhật cài đặt hiển thị văn bản thành công.", status=200)

@router.get("/settings/privacy", response_model=APIResponse[Any])
async def get_privacy(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.get_privacy_settings(current_user), message="Lấy cài đặt quyền riêng tư thành công.", status=200)

@router.put("/settings/privacy", response_model=APIResponse[Any])
async def update_privacy(data: PrivacyRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.update_privacy_settings(data.model_dump(), current_user), message="Cập nhật cài đặt quyền riêng tư thành công.", status=200)

@router.put("/settings", response_model=APIResponse[Any])
async def update_general_settings(data: SettingsUpdateRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.update_general_settings(data.settings, current_user), message="Cập nhật cài đặt thành công.", status=200)

@router.get("/history", response_model=APIResponse[Any])
async def get_history(skip: int = Query(0), limit: int = Query(20), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.get_reading_history(current_user, skip, limit), message="Lấy lịch sử đọc sách thành công.", status=200)

@router.post("/progress", response_model=APIResponse[Any])
async def update_progress(data: ProgressUpdate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.update_progress(data, current_user), message="Cập nhật tiến độ đọc sách thành công.", status=200)

@router.get("/stats", response_model=APIResponse[Any])
async def get_stats(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.get_reading_stats(current_user), message="Lấy số liệu thống kê đọc sách thành công.", status=200)

@router.get("/stats/chart", response_model=APIResponse[Any])
async def get_stats_chart(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.get_reading_stats_chart(current_user), message="Lấy biểu đồ thống kê đọc sách thành công.", status=200)

@router.post("/share-excerpt", response_model=APIResponse[Any])
async def share_excerpt(data: ExcerptShareRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.share_excerpt(data.model_dump(), current_user), message="Chia sẻ đoạn trích thành công.", status=201)

@router.post("/{document_id}/rate", response_model=APIResponse[Any])
async def rate_document(document_id: str, data: RatingCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.rate_document(document_id, data, current_user), message="Đánh giá tài liệu thành công.", status=200)

@router.post("/lists", response_model=APIResponse[Any])
async def create_reading_list(data: ReadingListCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.create_reading_list(data, current_user), message="Tạo danh sách đọc sách thành công.", status=201)

@router.get("/lists", response_model=APIResponse[Any])
async def get_my_reading_lists(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.get_my_reading_lists(current_user), message="Lấy danh sách đọc sách của bạn thành công.", status=200)

@router.get("/lists/{list_id}", response_model=APIResponse[Any])
async def get_reading_list_by_id(list_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.get_reading_list_by_id(list_id, current_user), message="Lấy chi tiết danh sách đọc thành công.", status=200)

@router.post("/documents/{document_id}/flashcards/generate", response_model=APIResponse[Any])
async def generate_flashcard(document_id: str, data: FlashcardGenerateRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.generate_flashcard(document_id, data, current_user), message="Tạo flashcard tự động thành công.", status=201)

@router.get("/search", response_model=APIResponse[Any])
async def semantic_search(q: str = Query(...), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.semantic_search(q, current_user), message="Tìm kiếm ngữ nghĩa thành công.", status=200)

@router.get("/continue-reading", response_model=APIResponse[Any])
async def get_continue_reading(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.get_continue_reading(current_user), message="Lấy danh sách tài liệu đang đọc thành công.", status=200)

@router.post("/bookmark-folders", response_model=APIResponse[Any])
async def create_bookmark_folder(data: BookmarkFolderCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.create_bookmark_folder(data.name, current_user), message="Tạo thư mục đánh dấu thành công.", status=201)

@router.get("/bookmark-folders", response_model=APIResponse[Any])
async def get_bookmark_folders(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.get_bookmark_folders(current_user), message="Lấy danh sách thư mục đánh dấu thành công.", status=200)

@router.put("/bookmark-folders/{folder_id}", response_model=APIResponse[Any])
async def assign_bookmarks_to_folder(folder_id: str, data: BookmarkFolderAssign, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.assign_bookmarks_to_folder(folder_id, data.bookmark_ids, current_user), message="Phân loại đánh dấu vào thư mục thành công.", status=200)

@router.delete("/bookmark-folders/{folder_id}", response_model=APIResponse[Any])
async def delete_bookmark_folder(folder_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.delete_bookmark_folder(folder_id, current_user), message="Xóa thư mục đánh dấu thành công.", status=200)

@router.post("/documents/{document_id}/chapters/rate", response_model=APIResponse[Any])
async def rate_chapter(document_id: str, data: ChapterRatingCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.rate_chapter(document_id, data, current_user), message="Đánh giá chương tài liệu thành công.", status=200)

@router.post("/documents/{document_id}/typo-report", response_model=APIResponse[Any])
async def report_typo(document_id: str, data: TypoReportCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.report_typo(document_id, data, current_user), message="Gửi báo cáo lỗi chính tả thành công.", status=201)

@router.get("/documents/{document_id}/typo-reports", response_model=APIResponse[Any])
async def get_typo_reports(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.get_typo_reports(document_id, current_user), message="Lấy danh sách báo cáo lỗi chính tả thành công.", status=200)

@router.post("/goals", response_model=APIResponse[Any])
async def set_reading_goal(data: ReadingGoalCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.set_reading_goal(data, current_user), message="Thiết lập mục tiêu đọc sách thành công.", status=201)

@router.get("/goals", response_model=APIResponse[Any])
async def get_reading_goal(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.get_reading_goal(current_user), message="Lấy thông tin mục tiêu đọc sách thành công.", status=200)

@router.put("/pinned-documents", response_model=APIResponse[Any])
async def set_pinned_documents(data: PinnedDocumentRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.set_pinned_documents(data.document_ids, current_user), message="Ghim tài liệu ưu tiên thành công.", status=200)

@router.get("/pinned-documents", response_model=APIResponse[Any])
async def get_pinned_documents(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.get_pinned_documents(current_user), message="Lấy danh sách tài liệu đã ghim thành công.", status=200)

@router.get("/documents/{document_id}/search", response_model=APIResponse[Any])
async def search_in_document(document_id: str, q: str = Query(...), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.search_in_document(document_id, q, current_user), message="Tìm kiếm trong tài liệu thành công.", status=200)
    
@router.post("/apply-author", response_model=APIResponse[Any])
async def apply_author(motivation: str = Body(..., embed=True), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.apply_for_author(motivation, current_user), message="Gửi đơn ứng tuyển thành công.", status=201)
