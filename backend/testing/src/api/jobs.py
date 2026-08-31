import httpx
from fastapi import APIRouter, Body, Depends, HTTPException

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope, get_project
from src.core.configuration import settings


router = APIRouter(prefix="/api/qa", tags=["QA Async Jobs"])
ALLOWED_EVENTS = {"document.parse.requested", "requirement.extract.requested", "requirement.semantic_diff.requested", "test.generate.requested", "duplicate.scan.requested", "impact.analysis.requested", "knowledge.index.requested"}
EVENT_PERMISSIONS = {
    "document.parse.requested": ("requirement_document.extract",),
    "requirement.extract.requested": ("requirement_document.extract",),
    "requirement.semantic_diff.requested": ("changeset.create",),
    "test.generate.requested": ("ai.generate_testcase", "testcase.create"),
    "duplicate.scan.requested": ("testcase.duplicate_check", "ai.run_duplicate_check"),
    "impact.analysis.requested": ("impact.execute", "ai.run_impact"),
    "knowledge.index.requested": ("knowledge.manage",),
}


@router.post("/projects/{project_id}/jobs", status_code=202)
async def enqueue_job(project_id: str, body: dict = Body(), user: CurrentUser = Depends(get_current_user)):
    event = body.get("event")
    if event not in ALLOWED_EVENTS:
        raise HTTPException(status_code=422, detail={"code": "UNSUPPORTED_JOB_EVENT"})
    for permission in EVENT_PERMISSIONS[event]:
        await get_project(project_id, user, permission)
    artifact_version_id = str(body.get("artifact_version_id") or "")
    model_version = str(body.get("model_version") or "")
    if not artifact_version_id or not model_version:
        raise HTTPException(status_code=422, detail={"code": "JOB_IDEMPOTENCY_FIELDS_REQUIRED"})
    payload = {"event": event, "project_id": project_id, "artifact_version_id": artifact_version_id, "model_version": model_version, "requester_id": user.id, "requester_email": user.email, "payload": body.get("payload") or {}}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{settings.WORKER_URL}/worker/internal/qa/jobs", headers={"X-Internal-Token": settings.SECRET_KEY}, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail={"code": "WORKER_UNAVAILABLE"}) from error
    return envelope(response.json())


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, user: CurrentUser = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{settings.WORKER_URL}/worker/internal/jobs/{job_id}", headers={"X-Internal-Token": settings.SECRET_KEY})
            response.raise_for_status()
            job = response.json()
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND"}) from error
        raise HTTPException(status_code=503, detail={"code": "WORKER_UNAVAILABLE"}) from error
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail={"code": "WORKER_UNAVAILABLE"}) from error
    project = await get_project(job.get("project_id", ""), user, "project.read")
    return envelope({**job, "project_id": project["_id"]})
