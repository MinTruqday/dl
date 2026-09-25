from fastapi import APIRouter, Depends, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.contracts import AttachmentCreate, AttachmentModeration
from src.services.attachment import AttachmentService

router = APIRouter(prefix="/kiem-thu", tags=["Tệp đính kèm kiểm thử"])


@router.post("/du-an/{project_id}/tep-dinh-kem", status_code=201)
async def register_attachment(
    project_id: str, payload: AttachmentCreate, user: CurrentUser = Depends(get_current_user)
):
    attachment = await AttachmentService.register(project_id, payload, user)
    return envelope(attachment, revision=attachment.get("revision", 1))


@router.get("/du-an/{project_id}/tep-dinh-kem")
async def list_attachments(
    project_id: str,
    artifact_type: str | None = Query(default=None, max_length=80),
    artifact_id: str | None = Query(default=None, max_length=200),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await AttachmentService.list(project_id, artifact_type, artifact_id, user))


@router.delete("/tep-dinh-kem/{attachment_id}")
async def delete_attachment(attachment_id: str, user: CurrentUser = Depends(get_current_user)):
    result, revision = await AttachmentService.delete(attachment_id, user)
    return envelope(result, revision=revision)


@router.post("/tep-dinh-kem/{attachment_id}/kiem-duyet")
async def moderate_attachment(
    attachment_id: str, payload: AttachmentModeration, user: CurrentUser = Depends(get_current_user)
):
    result, revision = await AttachmentService.moderate(attachment_id, payload, user)
    return envelope(result, revision=revision)
