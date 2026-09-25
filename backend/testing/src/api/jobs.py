from fastapi import APIRouter, Body, Depends, HTTPException

from src.clients.worker import WorkerClientError, worker_client
from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope, get_project
from src.services.job_policy import ALLOWED_JOB_EVENTS, JOB_EVENT_PERMISSIONS

router = APIRouter(prefix="/kiem-thu", tags=["Tác vụ kiểm thử bất đồng bộ"])


@router.post("/du-an/{project_id}/tac-vu", status_code=202)
async def enqueue_job(
    project_id: str, body: dict = Body(), user: CurrentUser = Depends(get_current_user)
):
    event = body.get("event")
    if event not in ALLOWED_JOB_EVENTS:
        raise HTTPException(status_code=422, detail={"code": "UNSUPPORTED_JOB_EVENT"})
    for permission in JOB_EVENT_PERMISSIONS[event]:
        await get_project(project_id, user, permission)
    artifact_version_id = str(body.get("artifact_version_id") or "")
    model_version = str(body.get("model_version") or "")
    if not artifact_version_id or not model_version:
        raise HTTPException(status_code=422, detail={"code": "JOB_IDEMPOTENCY_FIELDS_REQUIRED"})
    payload = {
        "event": event,
        "project_id": project_id,
        "artifact_version_id": artifact_version_id,
        "model_version": model_version,
        "requester_id": user.id,
        "requester_email": user.email,
        "payload": body.get("payload") or {},
    }
    try:
        job = await worker_client.enqueue(payload)
    except WorkerClientError as error:
        raise HTTPException(status_code=503, detail={"code": "WORKER_UNAVAILABLE"}) from error
    return envelope(job)


@router.get("/tac-vu/{job_id}")
async def get_job(job_id: str, user: CurrentUser = Depends(get_current_user)):
    try:
        job = await worker_client.get(job_id)
    except WorkerClientError as error:
        if error.status_code == 404:
            raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND"}) from error
        raise HTTPException(status_code=503, detail={"code": "WORKER_UNAVAILABLE"}) from error
    project = await get_project(job.get("project_id", ""), user, "project.read")
    return envelope({**job, "project_id": project["_id"]})
