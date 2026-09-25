from fastapi import APIRouter, Depends, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.contracts import ReviewCommentAction, ReviewCommentCreate, ReviewCommentPatch
from src.services.review_comment import ReviewCommentService

router = APIRouter(prefix="/kiem-thu", tags=["Rà soát kiểm thử"])


@router.post("/du-an/{project_id}/nhan-xet-ra-soat", status_code=201)
async def create_review_comment(
    project_id: str, payload: ReviewCommentCreate, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await ReviewCommentService.create(project_id, payload, user))


@router.get("/du-an/{project_id}/nhan-xet-ra-soat")
async def list_review_comments(
    project_id: str,
    artifact_type: str | None = Query(default=None, max_length=80),
    artifact_id: str | None = Query(default=None, max_length=200),
    status: str | None = Query(default="OPEN", max_length=20),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(
        await ReviewCommentService.list(project_id, artifact_type, artifact_id, status, user)
    )


@router.patch("/nhan-xet-ra-soat/{comment_id}")
async def update_review_comment(
    comment_id: str, payload: ReviewCommentPatch, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await ReviewCommentService.update(comment_id, payload, user))


@router.delete("/nhan-xet-ra-soat/{comment_id}")
async def delete_review_comment(comment_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(await ReviewCommentService.delete(comment_id, user))


@router.post("/nhan-xet-ra-soat/{comment_id}/giai-quyet")
async def resolve_review_comment(
    comment_id: str, payload: ReviewCommentAction, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await ReviewCommentService.resolve(comment_id, payload, user))


@router.post("/nhan-xet-ra-soat/{comment_id}/mo-lai")
async def reopen_review_comment(
    comment_id: str, payload: ReviewCommentAction, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await ReviewCommentService.reopen(comment_id, payload, user))
