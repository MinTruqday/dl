from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.database import database
from src.domain.schemas import ReviewCommentAction, ReviewCommentCreate, ReviewCommentPatch


router = APIRouter(prefix="/kiem-thu", tags=["Rà soát kiểm thử"])


@router.post("/du-an/{project_id}/nhan-xet-ra-soat", status_code=201)
async def create_review_comment(
    project_id: str,
    payload: ReviewCommentCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "comment.create")
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


@router.get("/du-an/{project_id}/nhan-xet-ra-soat")
async def list_review_comments(
    project_id: str,
    artifact_type: str | None = Query(default=None, max_length=80),
    artifact_id: str | None = Query(default=None, max_length=200),
    status: str | None = Query(default="OPEN", max_length=20),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "comment.read")
    query = {"project_id": project_id}
    if artifact_type:
        query["artifact_type"] = artifact_type
    if artifact_id:
        query["artifact_id"] = artifact_id
    if status:
        query["status"] = status
    comments = await database.value.review_comments.find(query).sort("created_at", 1).to_list(5000)
    return envelope(comments)


async def authorize_comment_change(comment: dict, user: CurrentUser):
    permission = "comment.update_own" if comment.get("author_id") == user.id else "comment.moderate"
    await get_project(comment["project_id"], user, permission)


@router.patch("/nhan-xet-ra-soat/{comment_id}")
async def update_review_comment(
    comment_id: str,
    payload: ReviewCommentPatch,
    user: CurrentUser = Depends(get_current_user),
):
    comment = await get_project_entity("review_comments", comment_id, user, "comment.read")
    await authorize_comment_change(comment, user)
    if comment.get("deleted_at"):
        raise HTTPException(status_code=409, detail={"code": "COMMENT_DELETED"})
    await database.value.review_comments.update_one(
        {"_id": comment_id, "project_id": comment["project_id"]},
        {"$set": {"body_doc": payload.body_doc, "edited_at": now(), "updated_at": now()}},
    )
    await audit(
        user.id,
        "review_comment_updated",
        "ReviewComment",
        comment_id,
        comment["project_id"],
    )
    return envelope(await database.value.review_comments.find_one({"_id": comment_id}))


@router.delete("/nhan-xet-ra-soat/{comment_id}")
async def delete_review_comment(
    comment_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    comment = await get_project_entity("review_comments", comment_id, user, "comment.read")
    permission = "comment.delete_own" if comment.get("author_id") == user.id else "comment.moderate"
    await get_project(comment["project_id"], user, permission)
    await database.value.review_comments.update_one(
        {"_id": comment_id, "project_id": comment["project_id"]},
        {
            "$set": {
                "body_doc": {"type": "doc", "content": []},
                "status": "DELETED",
                "deleted_by": user.id,
                "deleted_at": now(),
                "updated_at": now(),
            }
        },
    )
    await audit(
        user.id,
        "review_comment_deleted",
        "ReviewComment",
        comment_id,
        comment["project_id"],
    )
    return envelope({"deleted": True, "comment_id": comment_id})


@router.post("/nhan-xet-ra-soat/{comment_id}/giai-quyet")
async def resolve_review_comment(
    comment_id: str,
    payload: ReviewCommentAction,
    user: CurrentUser = Depends(get_current_user),
):
    comment = await get_project_entity("review_comments", comment_id, user, "comment.read")
    await authorize_comment_change(comment, user)
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


@router.post("/nhan-xet-ra-soat/{comment_id}/mo-lai")
async def reopen_review_comment(
    comment_id: str,
    payload: ReviewCommentAction,
    user: CurrentUser = Depends(get_current_user),
):
    comment = await get_project_entity("review_comments", comment_id, user, "comment.read")
    await authorize_comment_change(comment, user)
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
