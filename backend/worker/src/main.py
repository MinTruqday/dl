import hmac
import hashlib
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, database, init_db, record_job
from src.core.infrastructure.mq import mq
from src.core.metrics import PrometheusMiddleware, metrics_endpoint
from src.jobs.task import worker_runner


def require_internal_token(x_internal_token: str = Header(default="")):
    if not (
        settings.SECRET_KEY
        and x_internal_token
        and hmac.compare_digest(x_internal_token, settings.SECRET_KEY)
    ):
        raise HTTPException(status_code=403, detail="Invalid internal token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        await worker_runner.start()
        yield
    finally:
        await worker_runner.close()
        await mq.aclose()
        await close_db()


app = FastAPI(
    title="DocLib Worker",
    version=settings.VERSION,
    lifespan=lifespan,
)
app.add_middleware(PrometheusMiddleware, service_name="worker")
app.add_route("/metrics", metrics_endpoint("worker"))


class AssessmentCalibrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(min_length=1, max_length=128)
    owner_email: str = Field(min_length=1, max_length=320)
    payload: dict


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "healthy", "service": "worker"}


@app.get("/ready", include_in_schema=False)
async def ready():
    checks = {}
    try:
        await database.mongodb.admin.command("ping")
        checks["mongodb"] = "ready"
    except Exception:
        checks["mongodb"] = "unavailable"
    try:
        await mq.get_queue("assessment_calibration_queue")
        checks["rabbitmq"] = "ready"
    except Exception:
        checks["rabbitmq"] = "unavailable"
    checks["consumers"] = "ready" if worker_runner.is_running() else "unavailable"
    ready_state = all(value == "ready" for value in checks.values())
    return JSONResponse(
        status_code=200 if ready_state else 503,
        content={
            "status": "ready" if ready_state else "degraded",
            "service": "worker",
            "checks": checks,
        },
    )


@app.post(
    "/worker/internal/assessment/calibration",
    dependencies=[Depends(require_internal_token)],
    status_code=202,
)
async def enqueue_assessment_calibration(payload: AssessmentCalibrationRequest):
    idempotency_key = str(payload.payload.get("idempotency_key") or "")
    job_id = f"calibration-{hashlib.sha256(idempotency_key.encode()).hexdigest()[:40]}" if idempotency_key else f"calibration-{uuid.uuid4()}"
    existing = await database.mongodb[settings.WORKER_DB_NAME].worker_jobs.find_one({"_id": job_id})
    if existing:
        return {"job_id": job_id, "status": existing["status"]}
    task_payload = {"job_id": job_id, **payload.model_dump()}
    await record_job(job_id, {"status": "queued"}, {"kind": "assessment_calibration", "owner_id": payload.owner_id})
    try:
        await mq.publish("assessment_calibration_queue", task_payload)
    except Exception:
        await record_job(job_id, {"status": "failed", "error": "Queue unavailable"})
        raise HTTPException(status_code=503, detail="Worker queue is unavailable")
    return {"job_id": job_id, "status": "queued"}


@app.get(
    "/worker/internal/jobs/{job_id}",
    dependencies=[Depends(require_internal_token)],
)
async def get_job(job_id: str):
    if len(job_id) > 128:
        raise HTTPException(status_code=422, detail="Invalid job identifier")
    job = await database.mongodb[settings.WORKER_DB_NAME].worker_jobs.find_one(
        {"_id": job_id}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    for field in ["created_at", "updated_at", "attempt_started_at", "expire_at"]:
        value = job.get(field)
        if value:
            job[field] = value.isoformat()
    return job
