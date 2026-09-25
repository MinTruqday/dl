from fastapi import HTTPException

from src.core.auth import CurrentUser
from src.core.common import audit, get_project, get_project_entity, get_project_role, new_id, now
from src.repositories import test_design_repository
from src.services.domain_policy import domain_policy
from src.domain.contracts import AttachmentCreate, AttachmentModeration


class AttachmentService:
    artifact_collections = domain_policy("test_design")["attachment_artifact_collections"]
    policy = domain_policy("attachment")

    @staticmethod
    async def register(project_id: str, payload: AttachmentCreate, user: CurrentUser):
        await get_project(project_id, user, "attachment.upload")
        if (payload.artifact_type is None) != (payload.artifact_id is None):
            raise HTTPException(
                status_code=422,
                detail={"code": AttachmentService.policy["reference_incomplete_code"]},
            )
        if payload.artifact_type and payload.artifact_id:
            collection = AttachmentService.artifact_collections.get(payload.artifact_type)
            if not collection:
                raise HTTPException(
                    status_code=422,
                    detail={"code": AttachmentService.policy["artifact_type_invalid_code"]},
                )
            if not await test_design_repository.artifact_exists(
                collection, project_id, payload.artifact_id
            ):
                raise HTTPException(
                    status_code=404,
                    detail={"code": AttachmentService.policy["artifact_not_found_code"]},
                )
        existing = await test_design_repository.find_active_attachment(
            project_id,
            user.id,
            payload.url,
            AttachmentService.policy["active_status"],
        )
        if existing:
            return existing
        attachment = {
            "_id": new_id(AttachmentService.policy["id_prefix"]),
            "project_id": project_id,
            "owner_id": user.id,
            **payload.model_dump(),
            "status": AttachmentService.policy["active_status"],
            "revision": AttachmentService.policy["initial_revision"],
            "created_at": now(),
            "updated_at": now(),
        }
        await test_design_repository.insert_attachment(attachment)
        await audit(
            user.id,
            "attachment_registered",
            "Attachment",
            attachment["_id"],
            project_id,
            {"artifact_type": payload.artifact_type, "artifact_id": payload.artifact_id},
        )
        return attachment

    @staticmethod
    async def list(
        project_id: str,
        artifact_type: str | None,
        artifact_id: str | None,
        user: CurrentUser,
    ):
        await get_project(project_id, user, "attachment.read")
        query = {"project_id": project_id, "status": AttachmentService.policy["active_status"]}
        role = await get_project_role(project_id, user.id)
        if role == AttachmentService.policy["viewer_role"] and artifact_type == "defect":
            return []
        if role == AttachmentService.policy["viewer_role"]:
            query["artifact_type"] = {"$ne": "defect"}
        if artifact_type:
            query["artifact_type"] = artifact_type
        if artifact_id:
            query["artifact_id"] = artifact_id
        return await test_design_repository.list_attachments(query)

    @staticmethod
    async def delete(attachment_id: str, user: CurrentUser):
        attachment = await get_project_entity(
            AttachmentService.policy["collection"], attachment_id, user, "attachment.read"
        )
        permission = (
            "attachment.delete_own_unreferenced"
            if attachment.get("owner_id") == user.id
            else "attachment.moderate"
        )
        await get_project(attachment["project_id"], user, permission)
        if attachment.get("artifact_id"):
            raise HTTPException(
                status_code=409,
                detail={"code": AttachmentService.policy["referenced_immutable_code"]},
            )
        updated = await AttachmentService._mark_deleted(attachment_id, attachment, user.id)
        await audit(
            user.id, "attachment_deleted", "Attachment", attachment_id, attachment["project_id"]
        )
        return {"deleted": True, "attachment_id": attachment_id}, updated["revision"]

    @staticmethod
    async def moderate(
        attachment_id: str,
        payload: AttachmentModeration,
        user: CurrentUser,
    ):
        attachment = await get_project_entity(
            AttachmentService.policy["collection"], attachment_id, user, "attachment.moderate"
        )
        if attachment.get("status") == AttachmentService.policy["deleted_status"]:
            return {
                "deleted": True,
                "attachment_id": attachment_id,
            }, attachment.get("revision", AttachmentService.policy["initial_revision"])
        updated = await AttachmentService._mark_deleted(
            attachment_id, attachment, user.id, payload.reason
        )
        await audit(
            user.id,
            "attachment_moderated",
            "Attachment",
            attachment_id,
            attachment["project_id"],
            {"reason": payload.reason},
        )
        return {"deleted": True, "attachment_id": attachment_id}, updated["revision"]

    @staticmethod
    async def _mark_deleted(
        attachment_id: str,
        attachment: dict,
        actor_id: str,
        reason: str | None = None,
    ):
        changes = {
            "status": AttachmentService.policy["deleted_status"],
            "deleted_by": actor_id,
            "deleted_at": now(),
            "updated_at": now(),
        }
        if reason is not None:
            changes["moderation_reason"] = reason
        updated = await test_design_repository.mark_attachment_deleted(
            attachment_id,
            attachment["project_id"],
            attachment.get("revision", AttachmentService.policy["initial_revision"]),
            AttachmentService.policy["active_status"],
            changes,
        )
        if not updated:
            raise HTTPException(
                status_code=409,
                detail={"code": AttachmentService.policy["revision_conflict_code"]},
            )
        return updated
