from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, status
from typing import List, Any
from models.user import UserInDB
from models.comment import ReviewCreate, ReviewResponse
from api.dependency import get_current_user
from services.review import ReviewService

router = APIRouter(prefix="/reading")

@router.post("/{document_id}/review", response_model=APIResponse[ReviewResponse])
async def create_document_review(document_id: str, review_in: ReviewCreate, current_user: UserInDB = Depends(get_current_user)) -> Any:
    return APIResponse(data=await ReviewService.create_review(document_id, review_in, current_user), message="Gửi đánh giá tài liệu thành công.", status=201)

@router.get("/{document_id}/reviews", response_model=APIResponse[List[ReviewResponse]])
async def get_document_reviews(document_id: str) -> Any:
    return APIResponse(data=await ReviewService.get_reviews(document_id), message="Lấy danh sách đánh giá tài liệu thành công.", status=200)
