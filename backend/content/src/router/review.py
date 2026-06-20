from typing import Any, List

from fastapi import APIRouter, Depends, status
from src.router.dependency import get_current_user, get_db
from src.schemas.review import ReviewCreate, ReviewResponse
from src.services.review import ReviewManager

from core.response import APIResponse
from core.schemas.user import UserInDB

router = APIRouter(prefix="/reviews")


@router.post("/{document_id}", response_model=APIResponse[ReviewResponse])
async def create_document_review(
    document_id: str,
    review_in: ReviewCreate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
) -> Any:
    return APIResponse(
        data=await ReviewManager.create_review(
            document_id, review_in, current_user, db=db
        ),
        message="Gửi đánh giá cá nhân thành công",
        status=201,
    )


@router.get("/{document_id}", response_model=APIResponse[List[ReviewResponse]])
async def get_document_reviews(document_id: str, db=Depends(get_db)) -> Any:
    return APIResponse(
        data=await ReviewManager.get_reviews(document_id, db=db),
        message="Lấy danh sách đánh giá công khai thành công",
        status=200,
    )
