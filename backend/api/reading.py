from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from models.user import UserInDB
from api.dependencies import get_current_user
from services.reader import ReaderService
from core.database import db_client

router = APIRouter(prefix="/reading")

class ReadingListCreate(BaseModel):
    name: str
    description: str = None
    is_public: bool = True

class ProgressData(BaseModel):
    document_id: str
    progress_percentage: float
    current_chapter_slug: str = None

class RateDocumentData(BaseModel):
    rating: int
    review_text: str = None
    comment: str = None

@router.post("/lists", response_model=APIResponse[Any])
async def create_list(data: ReadingListCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.create_reading_list(data, current_user), message="Tạo danh sách đọc sách thành công.", status=201)

@router.get("/lists", response_model=APIResponse[Any])
async def get_my_lists(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.get_my_reading_lists(current_user), message="Lấy danh sách đọc sách của bạn thành công.", status=200)

@router.post("/lists/{list_id}/documents", response_model=APIResponse[Any])
async def add_document(list_id: str, document_id: str = Body(..., embed=True), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.add_document_to_list(list_id, document_id, current_user), message="Thêm tài liệu vào danh sách đọc thành công.", status=200)

@router.delete("/lists/{list_id}/documents/{document_id}", response_model=APIResponse[Any])
async def remove_document(list_id: str, document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.remove_document_from_list(list_id, document_id, current_user), message="Xóa tài liệu khỏi danh sách đọc thành công.", status=200)

@router.post("/progress", response_model=APIResponse[Any])
async def update_progress(data: ProgressData, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.update_progress(data, current_user), message="Cập nhật tiến độ đọc sách thành công.", status=200)

@router.get("/history", response_model=APIResponse[Any])
async def get_history(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.get_reading_history(current_user), message="Lấy lịch sử đọc sách thành công.", status=200)

@router.post("/{document_id}/rate", response_model=APIResponse[Any])
async def rate_document(document_id: str, data: RateDocumentData, current_user: UserInDB = Depends(get_current_user)):
    if data.review_text is None and data.comment is not None:
        data.review_text = data.comment
    return APIResponse(data=await ReaderService.rate_document(document_id, data, current_user), message="Đánh giá tài liệu thành công.", status=200)

@router.post("/{document_id}/review", response_model=APIResponse[Any])
async def review_document(document_id: str, data: RateDocumentData, current_user: UserInDB = Depends(get_current_user)):
    if data.review_text is None and data.comment is not None:
        data.review_text = data.comment
    return APIResponse(data=await ReaderService.rate_document(document_id, data, current_user), message="Gửi nhận xét tài liệu thành công.", status=200)

@router.get("/{document_id}/reviews", response_model=APIResponse[Any])
async def get_document_reviews(document_id: str):
    return APIResponse(data=await ReaderService.get_document_reviews(document_id), message="Lấy danh sách nhận xét tài liệu thành công.", status=200)

@router.post("/flashcards/review", response_model=APIResponse[Any])
async def review_flashcard(payload: dict = Body(...), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.review_flashcard(payload, current_user), message="Ôn tập flashcard thành công.", status=200)

@router.get("/recommendations", response_model=APIResponse[Any])
async def get_recommendations(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReaderService.get_reading_history(current_user), message="Lấy danh sách đề xuất đọc sách thành công.", status=200)