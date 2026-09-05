from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import ReturnDocument

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.database import database
from src.domain.schemas import AttachmentCreate, AttachmentModeration


router = APIRouter(prefix="/kiem-thu", tags=["Tệp đính kèm kiểm thử"])


@router.post("/du-an/{project_id}/tep-dinh-kem", status_code=201)
async def register_attachment(
    project_id: str,
    payload: AttachmentCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "attachment.upload")
    if (payload.artifact_type is None) != (payload.artifact_id is None):
        raise HTTPException(status_code=422, detail={"code": "ATTACHMENT_REFERENCE_INCOMPLETE"})
    if payload.artifact_type and payload.artifact_id:
        collections = {
            "requirement": "requirements",
            "requirement_document": "requirement_documents",
            "test_case_draft": "test_case_drafts",
            "test_case_version": "test_case_versions",
            "test_result": "test_results",
            "defect": "defects",
            "review_comment": "review_comments",
        }
        collection = collections.get(payload.artifact_type)
        if not collection:
            raise HTTPException(status_code=422, detail={"code": "ATTACHMENT_ARTIFACT_TYPE_INVALID"})
        artifact = await database.value[collection].find_one(
            {"_id": payload.artifact_id, "project_id": project_id}, {"_id": 1}
        )
        if not artifact:
            raise HTTPException(status_code=404, detail={"code": "ATTACHMENT_ARTIFACT_NOT_FOUND"})
    existing = await database.value.attachments.find_one(
        {"project_id": project_id, "owner_id": user.id, "url": payload.url, "status": "ACTIVE"}
    )
    if existing:
        return envelope(existing, revision=existing.get("revision", 1))
    attachment = {
        "_id": new_id("ATT"),
        "project_id": project_id,
        "owner_id": user.id,
        **payload.model_dump(),
        "status": "ACTIVE",
        "revision": 1,
        "created_at": now(),
        "updated_at": now(),
    }
    await database.value.attachments.insert_one(attachment)
    await audit(user.id, "attachment_registered", "Attachment", attachment["_id"], project_id, {"artifact_type": payload.artifact_type, "artifact_id": payload.artifact_id})
    return envelope(attachment, revision=1)


@router.get("/du-an/{project_id}/tep-dinh-kem")
async def list_attachments(
    project_id: str,
    artifact_type: str | None = Query(default=None, max_length=80),
    artifact_id: str | None = Query(default=None, max_length=200),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "attachment.read")
    query = {"project_id": project_id, "status": "ACTIVE"}
    if artifact_type:
        query["artifact_type"] = artifact_type
    if artifact_id:
        query["artifact_id"] = artifact_id
    return envelope(await database.value.attachments.find(query).sort("created_at", -1).to_list(5000))


@router.delete("/tep-dinh-kem/{attachment_id}")
async def delete_attachment(
    attachment_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    attachment = await get_project_entity("attachments", attachment_id, user, "attachment.read")
    permission = (
        "attachment.delete_own_unreferenced"
        if attachment.get("owner_id") == user.id
        else "attachment.moderate"
    )
    await get_project(attachment["project_id"], user, permission)
    if attachment.get("artifact_id"):
        raise HTTPException(status_code=409, detail={"code": "ATTACHMENT_REFERENCED_IMMUTABLE"})
    updated = await database.value.attachments.find_one_and_update(
        {"_id": attachment_id, "project_id": attachment["project_id"], "status": "ACTIVE", "revision": attachment.get("revision", 1)},
        {"$set": {"status": "DELETED", "deleted_by": user.id, "deleted_at": now(), "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "ATTACHMENT_REVISION_CONFLICT"})
    await audit(user.id, "attachment_deleted", "Attachment", attachment_id, attachment["project_id"])
    return envelope({"deleted": True, "attachment_id": attachment_id}, revision=updated["revision"])


@router.post("/tep-dinh-kem/{attachment_id}/kiem-duyet")
async def moderate_attachment(
    attachment_id: str,
    payload: AttachmentModeration,
    user: CurrentUser = Depends(get_current_user),
):
    attachment = await get_project_entity("attachments", attachment_id, user, "attachment.moderate")
    if attachment.get("status") == "DELETED":
        return envelope({"deleted": True, "attachment_id": attachment_id})
    updated = await database.value.attachments.find_one_and_update(
        {"_id": attachment_id, "project_id": attachment["project_id"], "status": "ACTIVE", "revision": attachment.get("revision", 1)},
        {"$set": {"status": "DELETED", "deleted_by": user.id, "deleted_at": now(), "moderation_reason": payload.reason, "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "ATTACHMENT_REVISION_CONFLICT"})
    await audit(user.id, "attachment_moderated", "Attachment", attachment_id, attachment["project_id"], {"reason": payload.reason})
    return envelope({"deleted": True, "attachment_id": attachment_id}, revision=updated["revision"])
