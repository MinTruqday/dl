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

@router.post("/lists")
async def create_list(data: ReadingListCreate, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.create_reading_list(data, current_user)

@router.get("/lists")
async def get_my_lists(current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.get_my_reading_lists(current_user)

@router.post("/lists/{list_id}/documents")
async def add_document(list_id: str, document_id: str = Body(..., embed=True), current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.add_document_to_list(list_id, document_id, current_user)

@router.delete("/lists/{list_id}/documents/{document_id}")
async def remove_document(list_id: str, document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.remove_document_from_list(list_id, document_id, current_user)

@router.post("/progress")
async def update_progress(data: ProgressData, current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.update_progress(data, current_user)

@router.get("/history")
async def get_history(current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.get_reading_history(current_user)

@router.post("/{document_id}/rate")
async def rate_document(document_id: str, data: RateDocumentData, current_user: UserInDB = Depends(get_current_user)):
    if data.review_text is None and data.comment is not None:
        data.review_text = data.comment
    return await ReaderService.rate_document(document_id, data, current_user)

@router.post("/{document_id}/review")
async def review_document(document_id: str, data: RateDocumentData, current_user: UserInDB = Depends(get_current_user)):
    if data.review_text is None and data.comment is not None:
        data.review_text = data.comment
    return await ReaderService.rate_document(document_id, data, current_user)

@router.get("/{document_id}/reviews")
async def get_document_reviews(document_id: str):
    return await ReaderService.get_document_reviews(document_id)

@router.post("/flashcards/review")
async def review_flashcard(payload: dict = Body(...), current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.review_flashcard(payload, current_user)

@router.get("/recommendations")
async def get_recommendations(current_user: UserInDB = Depends(get_current_user)):
    return await ReaderService.get_reading_history(current_user)