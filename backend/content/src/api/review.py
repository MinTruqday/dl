from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, status
from typing import List, Any
from src.schemas.user import UserInDB
from src.schemas.review import ReviewCreate, ReviewResponse
from src.api.dependency import get_db, get_current_user
from src.services.review import ReviewService
router = APIRouter(prefix='/danh-gia')

@router.post('/{document_id}', response_model=APIResponse[ReviewResponse])
async def create_document_review(document_id: str, review_in: ReviewCreate, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)) -> Any:
    return APIResponse(data=await ReviewService.create_review(document_id, review_in, current_user, db=db), message='Gửi đánh giá tài liệu success', status=201)

@router.get('/{document_id}', response_model=APIResponse[List[ReviewResponse]])
async def get_document_reviews(document_id: str, db=Depends(get_db)) -> Any:
    return APIResponse(data=await ReviewService.get_reviews(document_id, db=db), message='Lấy danh sách đánh giá tài liệu success', status=200)