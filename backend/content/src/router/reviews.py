from typing import Any, List
from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends
from src.dependencies import get_current_user, get_db
from src.schemas.reviews import ReviewCreate, ReviewResponse
from src.services.reviews import ReviewService

router = APIRouter(prefix="/reviews")

@router.post("/{document_id}", response_model=APIResponse[ReviewResponse])
async def create_document_review(document_id: str, review_in: ReviewCreate, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)) -> Any:
    return APIResponse(
        data=await ReviewService.create_review(document_id, review_in, current_user, db=db),
        message="Personal evaluative review for document has been successfully submitted and permanently recorded",
        status=201,
    )

@router.get("/{document_id}", response_model=APIResponse[List[ReviewResponse]])
async def get_document_reviews(document_id: str, db=Depends(get_db)) -> Any:
    return APIResponse(
        data=await ReviewService.get_reviews(document_id, db=db),
        message="Public evaluative reviews associated with specified document successfully retrieved and aggregated",
        status=200,
    )