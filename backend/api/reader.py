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

@router.put("/settings/typography")
async def update_typography(data: TypographyRequest, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.update_typography(data.model_dump(), current_user)

@router.get("/settings/privacy")
async def get_privacy(current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.get_privacy_settings(current_user)

@router.put("/settings/privacy")
async def update_privacy(data: PrivacyRequest, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.update_privacy_settings(data.model_dump(), current_user)

@router.get("/history")
async def get_history(skip: int = Query(0), limit: int = Query(20), current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.get_reading_history(current_user, skip, limit)

@router.post("/progress")
async def update_progress(data: ProgressUpdate, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.update_progress(data, current_user)

@router.get("/stats")
async def get_stats(current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.get_reading_stats(current_user)

@router.get("/stats/chart")
async def get_stats_chart(current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.get_reading_stats_chart(current_user)

@router.post("/share-excerpt")
async def share_excerpt(data: ExcerptShareRequest, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.share_excerpt(data.model_dump(), current_user)

@router.post("/{document_id}/rate")
async def rate_document(document_id: str, data: RatingCreate, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.rate_document(document_id, data, current_user)

@router.post("/lists")
async def create_reading_list(data: ReadingListCreate, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.create_reading_list(data, current_user)

@router.get("/lists")
async def get_my_reading_lists(current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.get_my_reading_lists(current_user)

@router.post("/documents/{document_id}/flashcards/generate")
async def generate_flashcard(document_id: str, data: FlashcardGenerateRequest, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.generate_flashcard(document_id, data, current_user)

@router.get("/search")
async def semantic_search(q: str = Query(...), current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.semantic_search(q, current_user)

@router.get("/continue-reading")
async def get_continue_reading(current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.get_continue_reading(current_user)

@router.post("/bookmark-folders")
async def create_bookmark_folder(data: BookmarkFolderCreate, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.create_bookmark_folder(data.name, current_user)

@router.get("/bookmark-folders")
async def get_bookmark_folders(current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.get_bookmark_folders(current_user)

@router.put("/bookmark-folders/{folder_id}")
async def assign_bookmarks_to_folder(folder_id: str, data: BookmarkFolderAssign, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.assign_bookmarks_to_folder(folder_id, data.bookmark_ids, current_user)

@router.delete("/bookmark-folders/{folder_id}")
async def delete_bookmark_folder(folder_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.delete_bookmark_folder(folder_id, current_user)

@router.post("/documents/{document_id}/chapters/rate")
async def rate_chapter(document_id: str, data: ChapterRatingCreate, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.rate_chapter(document_id, data, current_user)

@router.post("/documents/{document_id}/typo-report")
async def report_typo(document_id: str, data: TypoReportCreate, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.report_typo(document_id, data, current_user)

@router.get("/documents/{document_id}/typo-reports")
async def get_typo_reports(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.get_typo_reports(document_id, current_user)

@router.post("/goals")
async def set_reading_goal(data: ReadingGoalCreate, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.set_reading_goal(data, current_user)

@router.get("/goals")
async def get_reading_goal(current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.get_reading_goal(current_user)

@router.put("/pinned-documents")
async def set_pinned_documents(data: PinnedDocumentRequest, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.set_pinned_documents(data.document_ids, current_user)

@router.get("/pinned-documents")
async def get_pinned_documents(current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.get_pinned_documents(current_user)

@router.get("/documents/{document_id}/search")
async def search_in_document(document_id: str, q: str = Query(...), current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.search_in_document(document_id, q, current_user)
