import hashlib
from datetime import datetime, timezone

from fastapi import HTTPException
from src.repositories.jobs import worker_job_repository
from src.core.infrastructure.mq import mq
from src.core.metrics import metrics_collector
from src.schemas import DiscardJobRequest, TestingJobRequest


class WorkerJobService:
    @staticmethod
    async def enqueue(payload: TestingJobRequest):
        event = payload.event.value
        idempotency_key = ":".join(
            [payload.project_id, payload.artifact_version_id, event, payload.model_version]
        )
        job_id = f"qa-{hashlib.sha256(idempotency_key.encode()).hexdigest()[:40]}"
        if existing := await worker_job_repository.find_one({"_id": job_id}):
            return {"job_id": job_id, "status": existing["status"]}
        task_payload = {"job_id": job_id, **payload.model_dump(mode="json")}
        await worker_job_repository.record(
            job_id,
            {"status": "queued"},
            {
                "kind": event,
                "project_id": payload.project_id,
                "requester_id": payload.requester_id,
                "request": task_payload,
            },
        )
        try:
            await mq.publish("qa_job_queue", task_payload)
            metrics_collector.change_queue_depth("qa_job_queue", 1)
        except Exception as error:
            await worker_job_repository.record(job_id, {"status": "failed", "error": "Queue unavailable"})
            raise HTTPException(status_code=503, detail="Worker queue is unavailable") from error
        return {"job_id": job_id, "status": "queued"}

    @staticmethod
    async def retry(job_id: str):
        WorkerJobService._validate_id(job_id)
        job = await worker_job_repository.find_one({"_id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.get("status") != "failed":
            raise HTTPException(status_code=409, detail="Only failed jobs can be retried")
        request = job.get("request")
        if not isinstance(request, dict):
            raise HTTPException(status_code=422, detail="Job payload is unavailable for retry")
        retry_count = int(job.get("manual_retry_count", 0))
        if retry_count >= 9:
            raise HTTPException(status_code=409, detail="Manual retry limit reached")
        await worker_job_repository.record(
            job_id,
            {
                "status": "queued",
                "manual_retry_count": retry_count + 1,
                "error": None,
                "error_code": None,
            },
        )
        await mq.publish("qa_job_queue", request)
        metrics_collector.change_queue_depth("qa_job_queue", 1)
        return {"job_id": job_id, "status": "queued", "manual_retry_count": retry_count + 1}

    @staticmethod
    async def cancel(job_id: str):
        WorkerJobService._validate_id(job_id)
        job = await worker_job_repository.find_one({"_id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.get("status") == "canceled":
            return {"job_id": job_id, "status": "canceled"}
        if job.get("status") != "queued":
            raise HTTPException(status_code=409, detail="Only queued jobs can be canceled")
        await worker_job_repository.record(job_id, {"status": "canceled", "canceled_at": datetime.now(timezone.utc)})
        return {"job_id": job_id, "status": "canceled"}

    @staticmethod
    async def get(job_id: str):
        WorkerJobService._validate_id(job_id)
        job = await worker_job_repository.find_one({"_id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        for field in ["created_at", "updated_at", "attempt_started_at", "expire_at"]:
            if value := job.get(field):
                job[field] = value.isoformat()
        return job

    @staticmethod
    async def list(project_id: str, status: str, kind: str, limit: int):
        query = {}
        if project_id:
            query["project_id"] = project_id
        if status:
            query["status"] = status.lower()
        if kind:
            query["kind"] = kind
        items = await worker_job_repository.list(query, limit)
        return {"items": items, "total": await worker_job_repository.count(query)}

    @staticmethod
    async def overview(project_id: str):
        match = {"project_id": project_id} if project_id else {}
        rows = await worker_job_repository.overview(match)
        return {
            "jobs_by_status": {row["_id"]: row["count"] for row in rows},
            "total": sum(row["count"] for row in rows),
        }

    @staticmethod
    async def discard(job_id: str, payload: DiscardJobRequest):
        WorkerJobService._validate_id(job_id)
        job = await worker_job_repository.discard(job_id, {
            "status": "discarded",
            "discard_reason": payload.reason,
            "discarded_by": payload.actor_id,
            "discarded_at": datetime.now(timezone.utc),
        })
        if not job:
            raise HTTPException(status_code=409, detail="Only failed jobs can be discarded")
        return job

    @staticmethod
    def _validate_id(job_id: str):
        if len(job_id) > 128:
            raise HTTPException(status_code=422, detail="Invalid job identifier")
