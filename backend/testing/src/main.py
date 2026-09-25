from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.analytics import router as analytics_router
from src.api.api_artifacts import router as api_artifacts_router
from src.api.attachments import router as attachments_router
from src.api.automation_execution import internal_router as internal_automation_router
from src.api.automation_execution import router as automation_execution_router
from src.api.automation_scripts import router as automation_scripts_router
from src.api.bulk import router as bulk_router
from src.api.changes import router as changes_router
from src.api.cicd import internal_router as internal_cicd_router
from src.api.cicd import router as cicd_router
from src.api.collaboration import router as collaboration_router
from src.api.connectors import router as connectors_router
from src.api.data_sets import router as data_sets_router
from src.api.defect_prevention import router as defect_prevention_router
from src.api.design_suggestions import router as design_suggestions_router
from src.api.device_matrices import router as device_matrices_router
from src.api.environment_incidents import router as environment_incidents_router
from src.api.execution import router as execution_router
from src.api.execution_context import router as execution_context_router
from src.api.internal_jobs import router as internal_jobs_router
from src.api.internal_admin import router as internal_admin_router
from src.api.jobs import router as jobs_router
from src.api.measurements import router as measurements_router
from src.api.non_functional_testing import router as non_functional_testing_router
from src.api.notifications import router as notifications_router
from src.api.operations import router as operations_router
from src.api.process_improvement import router as process_improvement_router
from src.api.projects import router as projects_router
from src.api.quality_evaluations import router as quality_evaluations_router
from src.api.requirements import router as requirements_router
from src.api.review_sessions import router as review_sessions_router
from src.api.reviews import router as reviews_router
from src.api.risk import router as risk_router
from src.api.templates import router as templates_router
from src.api.test_analysis import router as test_analysis_router
from src.api.test_completion import router as test_completion_router
from src.api.test_design import router as test_design_router
from src.api.test_monitoring import router as test_monitoring_router
from src.api.test_status_reports import router as test_status_reports_router
from src.api.test_strategy import router as test_strategy_router
from src.api.traceability import router as traceability_router
from src.api.webhooks import internal_router as internal_webhooks_router
from src.api.webhooks import router as webhooks_router
from src.core.ai_streaming import AIStreamingMiddleware
from src.core.common import failure_metadata, new_id
from src.core.configuration import settings
from src.core.database import close_database, connect_database, database
from src.core.function_ids import apply_function_ids
from src.core.metrics import PrometheusMiddleware, metrics_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_database()
    yield
    await close_database()


app = FastAPI(title="Veriq", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(AIStreamingMiddleware)
app.add_middleware(PrometheusMiddleware)
app.add_route("/so-lieu", metrics_endpoint)
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
app.include_router(reviews_router)
app.include_router(review_sessions_router)
app.include_router(measurements_router)
app.include_router(quality_evaluations_router)
app.include_router(defect_prevention_router)
app.include_router(environment_incidents_router)
app.include_router(non_functional_testing_router)
app.include_router(process_improvement_router)
app.include_router(data_sets_router)
app.include_router(device_matrices_router)
app.include_router(design_suggestions_router)
app.include_router(templates_router)
app.include_router(test_design_router)
app.include_router(test_strategy_router)
app.include_router(test_analysis_router)
app.include_router(test_monitoring_router)
app.include_router(test_status_reports_router)
app.include_router(test_completion_router)
app.include_router(traceability_router)
app.include_router(changes_router)
app.include_router(execution_router)
app.include_router(execution_context_router)
app.include_router(risk_router)
app.include_router(analytics_router)
app.include_router(automation_scripts_router)
app.include_router(connectors_router)
app.include_router(automation_execution_router)
app.include_router(internal_automation_router)
app.include_router(cicd_router)
app.include_router(internal_cicd_router)
app.include_router(collaboration_router)
app.include_router(attachments_router)
app.include_router(api_artifacts_router)
app.include_router(bulk_router)
app.include_router(internal_jobs_router)
app.include_router(internal_admin_router)
app.include_router(jobs_router)
app.include_router(notifications_router)
app.include_router(webhooks_router)
app.include_router(internal_webhooks_router)
app.include_router(operations_router)
apply_function_ids(app)


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
    operation = failure_metadata(code, error.status_code, detail)
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {"code": code, "message": message, "details": details},
            "trace_id": trace_id,
            **operation,
        },
        headers=error.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, error: RequestValidationError):
    trace_id = new_id("TRC")
    issues = error.errors()
    locations = [tuple(str(part) for part in issue.get("loc", ())) for issue in issues]
    messages = [str(issue.get("msg", "")) for issue in issues]
    code = "VALIDATION_ERROR"
    if any("INVALID_RISK_MODEL" in message for message in messages) or any(
        "risk_model" in location for location in locations
    ):
        code = "INVALID_RISK_MODEL"
    elif any(
        location
        and location[-1] == "reason"
        and ("quality" in request.url.path or "quyet-dinh-chat-luong" in request.url.path)
        for location in locations
    ):
        code = "QUALITY_DECISION_REASON_REQUIRED"
    elif any(
        location and location[-1] == "owner_id" and "hoan-tat-kiem-thu" in request.url.path
        for location in locations
    ):
        code = "RESIDUAL_RISK_OWNER_REQUIRED"
    elif any(
        location
        and location[-1] in {"resolution", "resolution_ref"}
        and ("finding" in request.url.path or "giai-quyet" in request.url.path)
        for location in locations
    ):
        code = "ANALYSIS_FINDING_RESOLUTION_REQUIRED"
    operation = failure_metadata(code, 422)
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {
                "error": {
                    "code": code,
                    "message": code
                    if code != "VALIDATION_ERROR"
                    else "Dữ liệu đầu vào không hợp lệ",
                    "details": {"issues": issues},
                },
                "trace_id": trace_id,
                **operation,
            }
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, error: Exception):
    trace_id = new_id("TRC")
    operation = failure_metadata("INTERNAL_SERVER_ERROR", 500)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Thao tác thất bại",
                "details": {},
            },
            "trace_id": trace_id,
            **operation,
        },
    )


@app.get("/suc-khoe", include_in_schema=False)
async def health():
    return {"status": "healthy", "service": "testing"}


@app.get("/san-sang", include_in_schema=False)
async def ready():
    try:
        if database.client is None:
            raise RuntimeError
        await database.client.admin.command("ping")
        return {"status": "ready", "service": "testing"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready", "service": "testing"})
