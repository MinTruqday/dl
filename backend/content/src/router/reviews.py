from typing import Any, List
from core.response import APIResponse
from fastapi import APIRouter, Depends
from core.dependency import get_current_user, get_db
from src.schemas.reviews import ReviewCreate, ReviewResponse
from src.services.reviews import ReviewService

router = APIRouter(prefix="/danh-gia")

@router.post("/{document_id}", response_model=APIResponse[ReviewResponse])
async def create_document_review(document_id: str, review_in: ReviewCreate, current_user: dict = Depends(get_current_user), db=Depends(get_db)) -> Any:
    return APIResponse(
        data=await ReviewService.create_review(document_id, review_in, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=201,
    )

@router.get("/{document_id}", response_model=APIResponse[List[ReviewResponse]])
async def get_document_reviews(document_id: str, db=Depends(get_db)) -> Any:
    return APIResponse(
        data=await ReviewService.get_reviews(document_id, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )