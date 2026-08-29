from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.database import database
from src.domain.schemas import ReviewCommentAction, ReviewCommentCreate


router = APIRouter(prefix="/api/qa", tags=["QA Review"])


@router.post("/projects/{project_id}/review-comments", status_code=201)
async def create_review_comment(
    project_id: str,
    payload: ReviewCommentCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "review.comment")
    comment = {
        "_id": new_id("RC"),
        "project_id": project_id,
        **payload.model_dump(),
        "author_id": user.id,
        "status": "OPEN",
        "created_at": now(),
        "updated_at": now(),
    }
    if payload.parent_comment_id:
        parent = await database.value.review_comments.find_one(
            {"_id": payload.parent_comment_id, "project_id": project_id}
        )
        if not parent:
            raise HTTPException(status_code=422, detail={"code": "PARENT_COMMENT_NOT_FOUND"})
    await database.value.review_comments.insert_one(comment)
    await audit(
        user.id,
        "review_comment_created",
        "ReviewComment",
        comment["_id"],
        project_id,
        {"artifact_type": payload.artifact_type, "artifact_id": payload.artifact_id},
    )
    return envelope(comment)


@router.get("/projects/{project_id}/review-comments")
async def list_review_comments(
    project_id: str,
    artifact_type: str | None = Query(default=None, max_length=80),
    artifact_id: str | None = Query(default=None, max_length=200),
    status: str | None = Query(default="OPEN", max_length=20),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "review.read")
    query = {"project_id": project_id}
    if artifact_type:
        query["artifact_type"] = artifact_type
    if artifact_id:
        query["artifact_id"] = artifact_id
    if status:
        query["status"] = status
    comments = await database.value.review_comments.find(query).sort("created_at", 1).to_list(5000)
    return envelope(comments)


@router.post("/review-comments/{comment_id}/resolve")
async def resolve_review_comment(
    comment_id: str,
    payload: ReviewCommentAction,
    user: CurrentUser = Depends(get_current_user),
):
    comment = await get_project_entity("review_comments", comment_id, user, "review.resolve")
    if comment["status"] == "RESOLVED":
        return envelope(comment)
    updated = await database.value.review_comments.find_one_and_update(
        {"_id": comment_id, "project_id": comment["project_id"], "status": "OPEN"},
        {"$set": {"status": "RESOLVED", "resolved_by": user.id, "resolution_reason": payload.reason, "resolved_at": now(), "updated_at": now()}},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "COMMENT_STATE_CONFLICT"})
    updated = await database.value.review_comments.find_one({"_id": comment_id})
    await audit(user.id, "review_comment_resolved", "ReviewComment", comment_id, comment["project_id"], {"reason": payload.reason})
    return envelope(updated)


@router.post("/review-comments/{comment_id}/reopen")
async def reopen_review_comment(
    comment_id: str,
    payload: ReviewCommentAction,
    user: CurrentUser = Depends(get_current_user),
):
    comment = await get_project_entity("review_comments", comment_id, user, "review.resolve")
    if comment["status"] == "OPEN":
        return envelope(comment)
    updated = await database.value.review_comments.find_one_and_update(
        {"_id": comment_id, "project_id": comment["project_id"], "status": "RESOLVED"},
        {"$set": {"status": "OPEN", "reopened_by": user.id, "reopen_reason": payload.reason, "reopened_at": now(), "updated_at": now()}},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "COMMENT_STATE_CONFLICT"})
    updated = await database.value.review_comments.find_one({"_id": comment_id})
    await audit(user.id, "review_comment_reopened", "ReviewComment", comment_id, comment["project_id"], {"reason": payload.reason})
    return envelope(updated)
