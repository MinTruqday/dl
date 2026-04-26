from fastapi import APIRouter, Depends, status
from typing import List, Any
from models.user import UserInDB
from models.comment import ReviewCreate, ReviewResponse
from api.dependencies import get_current_user
from services.review import ReviewService

router = APIRouter()

@router.post("/documents/{document_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def tao_danh_gia(document_id: str, review_in: ReviewCreate, current_user: UserInDB = Depends(get_current_user)) -> Any:
    return await ReviewService.create_review(document_id, review_in, current_user)

@router.get("/documents/{document_id}/reviews", response_model=List[ReviewResponse])
async def lay_danh_sach_danh_gia(document_id: str) -> Any:
    return await ReviewService.get_reviews(document_id)
