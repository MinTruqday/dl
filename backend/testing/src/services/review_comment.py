from fastapi import HTTPException

from src.core.auth import CurrentUser
from src.core.common import audit, get_project, get_project_entity, new_id, now
from src.repositories.review import review_repository
from src.domain.contracts import ReviewCommentAction, ReviewCommentCreate, ReviewCommentPatch
from src.services.domain_policy import domain_policy


COMMENT_POLICY = domain_policy("review_comment")


class ReviewCommentService:
    @staticmethod
    async def create(project_id: str, payload: ReviewCommentCreate, user: CurrentUser):
        await get_project(project_id, user, COMMENT_POLICY["create_permission"])
        if payload.parent_comment_id:
            parent = await review_repository.find_comment(
                payload.parent_comment_id, project_id
            )
            if not parent:
                raise HTTPException(
                    status_code=422,
                    detail={"code": COMMENT_POLICY["parent_not_found_code"]},
                )
        comment = {
            "_id": new_id(COMMENT_POLICY["id_prefix"]),
            "project_id": project_id,
            **payload.model_dump(),
            "author_id": user.id,
            "status": COMMENT_POLICY["open_status"],
            "created_at": now(),
            "updated_at": now(),
        }
        await review_repository.insert_comment(comment)
        await audit(
            user.id,
            COMMENT_POLICY["created_event"],
            COMMENT_POLICY["entity"],
            comment["_id"],
            project_id,
            {"artifact_type": payload.artifact_type, "artifact_id": payload.artifact_id},
        )
        return comment

    @staticmethod
    async def list(
        project_id: str,
        artifact_type: str | None,
        artifact_id: str | None,
        status: str | None,
        user: CurrentUser,
    ):
        await get_project(project_id, user, COMMENT_POLICY["read_permission"])
        query = {"project_id": project_id}
        if artifact_type:
            query["artifact_type"] = artifact_type
        if artifact_id:
            query["artifact_id"] = artifact_id
        if status:
            query["status"] = status
        return await review_repository.list_comments(query)

    @staticmethod
    async def update(comment_id: str, payload: ReviewCommentPatch, user: CurrentUser):
        comment = await ReviewCommentService._get_for_change(comment_id, user)
        if comment.get("deleted_at"):
            raise HTTPException(
                status_code=409, detail={"code": COMMENT_POLICY["deleted_code"]}
            )
        timestamp = now()
        updated = await review_repository.update_comment(
            comment_id,
            comment["project_id"],
            {"body_doc": payload.body_doc, "edited_at": timestamp, "updated_at": timestamp},
        )
        await audit(
            user.id,
            COMMENT_POLICY["updated_event"],
            COMMENT_POLICY["entity"],
            comment_id,
            comment["project_id"],
        )
        return updated

    @staticmethod
    async def delete(comment_id: str, user: CurrentUser):
        comment = await get_project_entity(
            COMMENT_POLICY["collection"],
            comment_id,
            user,
            COMMENT_POLICY["read_permission"],
        )
        permission = (
            COMMENT_POLICY["delete_own_permission"]
            if comment.get("author_id") == user.id
            else COMMENT_POLICY["moderate_permission"]
        )
        await get_project(comment["project_id"], user, permission)
        timestamp = now()
        await review_repository.mark_comment_deleted(
            comment_id,
            comment["project_id"],
            {
                "body_doc": {"type": "doc", "content": []},
                "status": COMMENT_POLICY["deleted_status"],
                "deleted_by": user.id,
                "deleted_at": timestamp,
                "updated_at": timestamp,
            },
        )
        await audit(
            user.id,
            COMMENT_POLICY["deleted_event"],
            COMMENT_POLICY["entity"],
            comment_id,
            comment["project_id"],
        )
        return {"deleted": True, "comment_id": comment_id}

    @staticmethod
    async def resolve(comment_id: str, payload: ReviewCommentAction, user: CurrentUser):
        return await ReviewCommentService._transition(
            comment_id,
            payload,
            user,
            COMMENT_POLICY["open_status"],
            COMMENT_POLICY["resolved_status"],
            "resolved",
            COMMENT_POLICY["resolved_event"],
        )

    @staticmethod
    async def reopen(comment_id: str, payload: ReviewCommentAction, user: CurrentUser):
        return await ReviewCommentService._transition(
            comment_id,
            payload,
            user,
            COMMENT_POLICY["resolved_status"],
            COMMENT_POLICY["open_status"],
            "reopened",
            COMMENT_POLICY["reopened_event"],
        )

    @staticmethod
    async def _get_for_change(comment_id: str, user: CurrentUser):
        comment = await get_project_entity(
            COMMENT_POLICY["collection"],
            comment_id,
            user,
            COMMENT_POLICY["read_permission"],
        )
        permission = (
            COMMENT_POLICY["update_own_permission"]
            if comment.get("author_id") == user.id
            else COMMENT_POLICY["moderate_permission"]
        )
        await get_project(comment["project_id"], user, permission)
        return comment

    @staticmethod
    async def _transition(
        comment_id: str,
        payload: ReviewCommentAction,
        user: CurrentUser,
        source: str,
        target: str,
        action: str,
        audit_action: str,
    ):
        comment = await ReviewCommentService._get_for_change(comment_id, user)
        if comment["status"] == target:
            return comment
        timestamp = now()
        updated = await review_repository.transition_comment(
            comment_id,
            comment["project_id"],
            source,
            {
                "status": target,
                f"{action}_by": user.id,
                f"{action}_at": timestamp,
                "resolution_reason"
                if target == COMMENT_POLICY["resolved_status"]
                else "reopen_reason": payload.reason,
                "updated_at": timestamp,
            },
        )
        if not updated:
            raise HTTPException(
                status_code=409, detail={"code": COMMENT_POLICY["state_conflict_code"]}
            )
        await audit(
            user.id,
            audit_action,
            COMMENT_POLICY["entity"],
            comment_id,
            comment["project_id"],
            {"reason": payload.reason},
        )
        return updated
