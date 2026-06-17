from typing import Any, List

from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends, status
from src.router.dependency_router import get_current_user, get_db
from src.schemas.review_schema import ReviewCreate, ReviewResponse
from src.services.review_service import ReviewService

router = APIRouter(prefix="/reviews")


@router.post("/{document_id}", response_model=APIResponse[ReviewResponse])
async def create_document_review(
    document_id: str,
    review_in: ReviewCreate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
) -> Any:
    return APIResponse(
        data=await ReviewService.create_review(
            document_id, review_in, current_user, db=db
        ),
        message="Your personal review for the document has been successfully submitted and recorded",
        status=201,
    )


@router.get("/{document_id}", response_model=APIResponse[List[ReviewResponse]])
async def get_document_reviews(document_id: str, db=Depends(get_db)) -> Any:
    return APIResponse(
        data=await ReviewService.get_reviews(document_id, db=db),
        message="The public reviews associated with the specified document have been successfully retrieved",
        status=200,
    )