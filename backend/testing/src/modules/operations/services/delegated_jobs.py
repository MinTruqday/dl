from fastapi import HTTPException

from src.clients.worker import WorkerClientError, worker_client
from src.core.auth import CurrentUser
from src.core.common import get_project
from src.modules.operations.services.job_policy import job_event_permissions


class DelegatedJobService:
    @staticmethod
    async def enqueue(project_id: str, body: dict, user: CurrentUser):
        
        event = body.get("event")
        permissions_by_event = job_event_permissions()
        if event not in permissions_by_event:
            raise HTTPException(status_code=422, detail={"code": 'UNSUPPORTED_JOB_EVENT'})
        for permission in permissions_by_event[event]:
            await get_project(project_id, user, permission)
        artifact_version_id = str(body.get("artifact_version_id") or "")
        model_version = str(body.get("model_version") or "")
        if not artifact_version_id or not model_version:
            raise HTTPException(
                status_code=422,
                detail={"code": 'JOB_IDEMPOTENCY_FIELDS_REQUIRED'},
            )
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
            return await worker_client.enqueue(payload)
        except WorkerClientError as error:
            raise HTTPException(
                status_code=503, detail={"code": 'WORKER_UNAVAILABLE'}
            ) from error

    @staticmethod
    async def get(job_id: str, user: CurrentUser):
        
        try:
            job = await worker_client.get(job_id)
        except WorkerClientError as error:
            if error.status_code == 404:
                raise HTTPException(
                    status_code=404, detail={"code": 'JOB_NOT_FOUND'}
                ) from error
            raise HTTPException(
                status_code=503, detail={"code": 'WORKER_UNAVAILABLE'}
            ) from error
        project = await get_project(job.get("project_id", ""), user, "project.read")
        return {**job, "project_id": project["_id"]}
