from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.analytics import router as analytics_router
from src.api.api_artifacts import router as api_artifacts_router
from src.api.changes import router as changes_router
from src.api.execution import router as execution_router
from src.api.internal_jobs import router as internal_jobs_router
from src.api.jobs import router as jobs_router
from src.api.projects import router as projects_router
from src.api.requirements import router as requirements_router
from src.api.test_design import router as test_design_router
from src.api.traceability import router as traceability_router
from src.core.common import new_id
from src.core.configuration import settings
from src.core.database import close_database, connect_database, database
from src.core.metrics import PrometheusMiddleware, metrics_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_database()
    yield
    await close_database()


app = FastAPI(title="Agentic AI Test Management", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", metrics_endpoint)
origins = [origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(projects_router)
app.include_router(requirements_router)
app.include_router(test_design_router)
app.include_router(traceability_router)
app.include_router(changes_router)
app.include_router(execution_router)
app.include_router(analytics_router)
app.include_router(api_artifacts_router)
app.include_router(internal_jobs_router)
app.include_router(jobs_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, error: HTTPException):
    trace_id = new_id("TRC")
    detail = error.detail
    if isinstance(detail, dict):
        code = detail.get("code", "REQUEST_FAILED")
        details = {key: value for key, value in detail.items() if key != "code"}
        message = detail.get("message") or code
    else:
        code = "REQUEST_FAILED"
        details = {}
        message = str(detail)
    return JSONResponse(status_code=error.status_code, content={"error": {"code": code, "message": message, "details": details}, "trace_id": trace_id}, headers=error.headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, error: RequestValidationError):
    trace_id = new_id("TRC")
    return JSONResponse(status_code=422, content=jsonable_encoder({"error": {"code": "VALIDATION_ERROR", "message": "Dữ liệu đầu vào không hợp lệ", "details": {"issues": error.errors()}}, "trace_id": trace_id}))


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "healthy", "service": "qa"}


@app.get("/ready", include_in_schema=False)
async def ready():
    try:
        if database.client is None:
            raise RuntimeError
        await database.client.admin.command("ping")
        return {"status": "ready", "service": "qa"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready", "service": "qa"})
