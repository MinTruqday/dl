from fastapi import HTTPException

from src.clients.worker import WorkerClientError, worker_client
from src.core.auth import CurrentUser
from src.core.common import get_project
from src.services.domain_policy import domain_policy
from src.services.job_policy import JOB_EVENT_PERMISSIONS


class DelegatedJobService:
    @staticmethod
    async def enqueue(project_id: str, body: dict, user: CurrentUser):
        policy = domain_policy("delegated_jobs")
        event = body.get("event")
        if event not in JOB_EVENT_PERMISSIONS:
            raise HTTPException(status_code=422, detail={"code": policy["unsupported_event_code"]})
        for permission in JOB_EVENT_PERMISSIONS[event]:
            await get_project(project_id, user, permission)
        artifact_version_id = str(body.get("artifact_version_id") or "")
        model_version = str(body.get("model_version") or "")
        if not artifact_version_id or not model_version:
            raise HTTPException(
                status_code=422,
                detail={"code": policy["idempotency_fields_required_code"]},
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
                status_code=503, detail={"code": policy["worker_unavailable_code"]}
            ) from error

    @staticmethod
    async def get(job_id: str, user: CurrentUser):
        policy = domain_policy("delegated_jobs")
        try:
            job = await worker_client.get(job_id)
        except WorkerClientError as error:
            if error.status_code == 404:
                raise HTTPException(
                    status_code=404, detail={"code": policy["job_not_found_code"]}
                ) from error
            raise HTTPException(
                status_code=503, detail={"code": policy["worker_unavailable_code"]}
            ) from error
        project = await get_project(job.get("project_id", ""), user, "project.read")
        return {**job, "project_id": project["_id"]}
